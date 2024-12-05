from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Literal
from pydantic import BaseModel, validator
import uuid
from sqlalchemy.orm import Session
from .database import SessionLocal, BackendDB
from .policies import BackendPolicy, RoundRobinPolicy, WeightedPolicy, AllActivePolicy, RandomPolicy
from enum import Enum
from .models import APIResponse

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Backend(BaseModel):
    id: str = str(uuid.uuid4())
    name: str
    host: str
    weight: Optional[int] = 1
    status: Literal["active", "down"] = "active"

    @validator('status')
    def validate_status(cls, v):
        if v not in ["active", "down"]:
            raise ValueError("Status must be either 'active' or 'down'")
        return v

    class Config:
        from_attributes = True

class PolicyType(str, Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    ALL_ACTIVE = "all_active"
    RANDOM = "random"

POLICY_MAP = {
    PolicyType.ROUND_ROBIN: RoundRobinPolicy(limit=1),
    PolicyType.WEIGHTED: WeightedPolicy(limit=3),
    PolicyType.ALL_ACTIVE: AllActivePolicy(limit=5),
    PolicyType.RANDOM: RandomPolicy(limit=1)
}

class BackendScheduler:
    def __init__(self, default_policy: BackendPolicy = None):
        self.default_policy = default_policy or AllActivePolicy()
    
    def add_backend(self, db: Session, app_id: str, backend: Backend):
        # Check if host already exists
        existing_backend = db.query(BackendDB).filter(BackendDB.host == backend.host).first()
        if existing_backend:
            raise HTTPException(status_code=400, detail="Backend with this host already exists")
            
        db_backend = BackendDB(
            id=backend.id,
            app_id=app_id,
            name=backend.name,
            host=backend.host,
            weight=backend.weight,
            status=backend.status
        )
        db.add(db_backend)
        db.commit()
        db.refresh(db_backend)
        
        # Refresh the session to ensure other queries get the latest data
        db.expire_all()
        return Backend.from_orm(db_backend)

    def get_backends(self, db: Session, app_id: str, policy: BackendPolicy = None) -> List[Backend]:
        # Refresh the session to ensure we get the latest data
        db.expire_all()
        db.refresh(db.query(BackendDB).filter(BackendDB.app_id == app_id).first())
        
        backends = db.query(BackendDB).filter(BackendDB.app_id == app_id).all()
        
        # Apply policy
        selected_policy = policy or self.default_policy
        selected_backends = selected_policy.select_backends(backends)
        
        return [Backend.from_orm(b) for b in selected_backends]

    def remove_backend(self, db: Session, app_id: str, backend_id: str):
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == app_id,
            BackendDB.id == backend_id
        ).first()
        if backend:
            db.delete(backend)
            db.commit()
            # Refresh the session to ensure other queries get the latest data
            db.expire_all()
        else:
            raise HTTPException(status_code=404, detail="Backend not found")

    def update_backend_status(self, db: Session, app_id: str, backend_id: str, status: str):
        if status not in ["active", "down"]:
            raise HTTPException(status_code=400, detail="Status must be either 'active' or 'down'")
        
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == app_id,
            BackendDB.id == backend_id
        ).first()
        
        if not backend:
            raise HTTPException(status_code=404, detail="Backend not found")
        
        backend.status = status
        db.commit()
        db.refresh(backend)
        db.expire_all()
        return Backend.from_orm(backend)

    def update_backend_app_id(self, db: Session, current_app_id: str, backend_id: str, new_app_id: str):
        if not new_app_id:
            raise HTTPException(status_code=400, detail="New app_id cannot be empty")
            
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == current_app_id,
            BackendDB.id == backend_id
        ).first()
        
        if not backend:
            raise HTTPException(status_code=404, detail="Backend not found")
            
        backend.app_id = new_app_id
        db.commit()
        db.refresh(backend)
        db.expire_all()
        return Backend.from_orm(backend)

    def update_policy_limit(self, policy_type: PolicyType, new_limit: int) -> APIResponse:
        """Update the limit of a specific policy"""
        try:
            policy = POLICY_MAP.get(policy_type)
            if not policy:
                return APIResponse.error("Policy not found")
                
            policy.update_limit(new_limit)
            return APIResponse.success(
                data={"policy": policy_type, "new_limit": new_limit},
                msg=f"Updated {policy_type} limit to {new_limit}"
            )
        except ValueError as e:
            return APIResponse.error(str(e))

    def get_supported_policies(self) -> APIResponse:
        """Get list of supported policies with their current limits"""
        policies_info = []
        for policy_type, policy in POLICY_MAP.items():
            policies_info.append({
                "type": policy_type,
                "limit": policy.limit,
                "description": policy.__doc__.strip() if policy.__doc__ else ""
            })
        return APIResponse.success(
            data=policies_info,
            msg="Successfully retrieved supported policies"
        )

    def get_all_backends(self, db: Session) -> APIResponse:
        """Get all backends regardless of app_id"""
        try:
            backends = db.query(BackendDB).all()
            return APIResponse.success(
                data=[Backend.from_orm(b) for b in backends],
                msg="Successfully retrieved all backends"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    def get_app_backends(self, db: Session, app_id: str) -> APIResponse:
        """Get all backends for a specific app_id"""
        try:
            backends = db.query(BackendDB).filter(BackendDB.app_id == app_id).all()
            return APIResponse.success(
                data=[Backend.from_orm(b) for b in backends],
                msg=f"Successfully retrieved backends for app_id: {app_id}"
            )
        except Exception as e:
            return APIResponse.error(str(e))

scheduler = BackendScheduler()

@router.post("/v1/{app_id}/backends")
async def add_backend(
    app_id: str,
    backend: Backend,
    db: Session = Depends(get_db)
):
    try:
        return scheduler.add_backend(db, app_id, backend)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/v1/{app_id}/backends")
async def get_backends(
    app_id: str,
    policy: Optional[PolicyType] = None,
    db: Session = Depends(get_db)
):
    selected_policy = POLICY_MAP.get(policy) if policy else None
    return scheduler.get_backends(db, app_id, policy=selected_policy)

@router.delete("/v1/{app_id}/backends/{backend_id}")
async def remove_backend(
    app_id: str,
    backend_id: str,
    db: Session = Depends(get_db)
):
    try:
        scheduler.remove_backend(db, app_id, backend_id)
        return {"message": "Backend removed successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}")
async def update_backend(
    app_id: str,
    backend_id: str,
    status: str,
    db: Session = Depends(get_db)
):
    try:
        return scheduler.update_backend_status(db, app_id, backend_id, status)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}/app")
async def update_backend_app(
    app_id: str,
    backend_id: str,
    new_app_id: str,
    db: Session = Depends(get_db)
):
    """
    Update the app_id of a backend to reassign it to a different service
    """
    try:
        return scheduler.update_backend_app_id(db, app_id, backend_id, new_app_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}/weight")
async def update_backend_weight(
    app_id: str,
    backend_id: str,
    weight: int,
    db: Session = Depends(get_db)
):
    """
    Update the weight of a backend for load balancing
    """
    try:
        return scheduler.update_backend_weight(db, app_id, backend_id, weight)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/v1/policies/{policy_type}/limit")
async def update_policy_limit(
    policy_type: PolicyType,
    new_limit: int
) -> APIResponse:
    """
    Update the limit of a backend selection policy
    """
    return scheduler.update_policy_limit(policy_type, new_limit)

@router.get("/v1/policies")
async def list_policies() -> APIResponse:
    """
    List all supported backend selection policies
    """
    return scheduler.get_supported_policies()

@router.get("/v1/backends")
async def list_all_backends(
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    List all backends in the system
    """
    return scheduler.get_all_backends(db)

@router.get("/v1/{app_id}/backends/all")
async def list_app_backends(
    app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    List all backends for a specific app_id without policy filtering
    """
    return scheduler.get_app_backends(db, app_id)