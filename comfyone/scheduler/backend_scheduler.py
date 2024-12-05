from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Literal
from pydantic import BaseModel, validator
import uuid
from sqlalchemy.orm import Session
from .database import SessionLocal, BackendDB
from .policies import BackendPolicy, RoundRobinPolicy, WeightedPolicy, AllActivePolicy, RandomPolicy
from enum import Enum
from .models import APIResponse
from .db_operations import DBOperations

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
    state: Literal["active", "down"] = "active"

    @validator('state')
    def validate_state(cls, v):
        if v not in ["active", "down"]:
            raise ValueError("State must be either 'active' or 'down'")
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
        self.default_policy = default_policy or RoundRobinPolicy(limit=1)
        self.db_ops = DBOperations()
    
    def add_backend(self, db: Session, app_id: str, backend: Backend) -> APIResponse:
        return self.db_ops.add_backend(db, app_id, backend)

    def get_backends(self, db: Session, app_id: str, policy: BackendPolicy = None) -> APIResponse:
        """Get backends filtered by policy"""
        try:
            backends_response = self.db_ops.get_app_backends(db, app_id)
            if backends_response.code != 0:
                return backends_response
            
            # Select backends based on policy, default to default_policy if no policy is provided
            # you can also pass a custom policy to the function optimize for different scenarios
            # default policy is RoundRobinPolicy(limit=1)
            selected_policy = policy or self.default_policy
            selected_backends = selected_policy.select_backends(backends_response.data)
            
            return APIResponse.success(
                data=[Backend.from_orm(b) for b in selected_backends],
                msg="Successfully retrieved backends"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    def get_all_backends(self, db: Session) -> APIResponse:
        return self.db_ops.get_all_backends(db)

    def get_app_backends(self, db: Session, app_id: str) -> APIResponse:
        return self.db_ops.get_app_backends(db, app_id)

    def remove_backend(self, db: Session, app_id: str, backend_id: str) -> APIResponse:
        return self.db_ops.remove_backend(db, app_id, backend_id)

    def update_backend_state(self, db: Session, app_id: str, backend_id: str, state: str) -> APIResponse:
        return self.db_ops.update_backend_state(db, app_id, backend_id, state)

    def update_backend_app_id(self, db: Session, current_app_id: str, backend_id: str, new_app_id: str) -> APIResponse:
        return self.db_ops.update_backend_app_id(db, current_app_id, backend_id, new_app_id)

    def update_backend_weight(self, db: Session, app_id: str, backend_id: str, weight: int) -> APIResponse:
        return self.db_ops.update_backend_weight(db, app_id, backend_id, weight)

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

scheduler = BackendScheduler()

# Backend Management APIs
@router.post("/v1/{app_id}/backends")
async def add_backend(
    app_id: str,
    backend: Backend,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Add a new backend to the system"""
    try:
        result = scheduler.add_backend(db, app_id, backend)
        return APIResponse.success(data=result, msg="Backend added successfully")
    except Exception as e:
        return APIResponse.error(str(e))

@router.get("/v1/backends")
async def list_all_backends(
    db: Session = Depends(get_db)
) -> APIResponse:
    """List all backends in the system"""
    return scheduler.get_all_backends(db)

@router.get("/v1/{app_id}/backends/all")
async def list_app_backends(
    app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """List all backends for a specific app_id without policy filtering"""
    return scheduler.get_app_backends(db, app_id)

@router.get("/v1/{app_id}/backends")
async def get_backends(
    app_id: str,
    policy: Optional[PolicyType] = None,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Get backends filtered by policy"""
    selected_policy = POLICY_MAP.get(policy) if policy else None
    result = scheduler.get_backends(db, app_id, policy=selected_policy)
    return APIResponse.success(data=result, msg="Successfully retrieved backends")

@router.delete("/v1/{app_id}/backends/{backend_id}")
async def remove_backend(
    app_id: str,
    backend_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Remove a backend from the system"""
    try:
        scheduler.remove_backend(db, app_id, backend_id)
        return APIResponse.success(msg="Backend removed successfully")
    except Exception as e:
        return APIResponse.error(str(e))

# Backend Configuration APIs
@router.patch("/v1/{app_id}/backends/{backend_id}")
async def update_backend_status(
    app_id: str,
    backend_id: str,
    status: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update backend status (active/down)"""
    try:
        result = scheduler.update_backend_status(db, app_id, backend_id, status)
        return APIResponse.success(data=result, msg=f"Backend status updated to {status}")
    except Exception as e:
        return APIResponse.error(str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}/app")
async def update_backend_app(
    app_id: str,
    backend_id: str,
    new_app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update the app_id of a backend"""
    try:
        result = scheduler.update_backend_app_id(db, app_id, backend_id, new_app_id)
        return APIResponse.success(data=result, msg=f"Backend app_id updated to {new_app_id}")
    except Exception as e:
        return APIResponse.error(str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}/weight")
async def update_backend_weight(
    app_id: str,
    backend_id: str,
    weight: int,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update backend weight for load balancing"""
    try:
        result = scheduler.update_backend_weight(db, app_id, backend_id, weight)
        return APIResponse.success(data=result, msg=f"Backend weight updated to {weight}")
    except Exception as e:
        return APIResponse.error(str(e))

# Policy Management APIs
@router.get("/v1/policies")
async def list_policies() -> APIResponse:
    """List all supported backend selection policies"""
    return scheduler.get_supported_policies()

@router.patch("/v1/policies/{policy_type}/limit")
async def update_policy_limit(
    policy_type: PolicyType,
    new_limit: int
) -> APIResponse:
    """Update the limit of a backend selection policy"""
    return scheduler.update_policy_limit(policy_type, new_limit)