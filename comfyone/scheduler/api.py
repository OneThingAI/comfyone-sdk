import logging
from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import ValidationError
from .database import SessionLocal
from .backend_scheduler import BackendScheduler
from .models import Backend, Policy, APIResponse
from ..utils.logging import setup_logger

router = APIRouter()
logger = setup_logger(name="scheduler", level=logging.INFO)

def setup_log_level(level: int):
    logger.setLevel(level)

# Dependency to get DB session
def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()

scheduler = BackendScheduler()

# Backend Management APIs
@router.post("/v1/backends")
async def add_backend(
    backend: Backend,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Add a new backend to the system"""
    try:
        logger.debug(f"Received backend data: {backend.dict()}")
        backend_ret, policy_ret = scheduler.add_backend(db, backend)
        backend_policy_ret = {
            "backend": backend_ret,
            "policy": policy_ret
        }
        return APIResponse.success(data=backend_policy_ret, msg="Backend added successfully")
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIResponse.error(f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while adding backend: {str(e)}")
        return APIResponse.error(str(e))

@router.get("/v1/backends/all")
async def list_all_backends(
    db: Session = Depends(get_db)
) -> APIResponse:
    """List all backends in the system"""
    return APIResponse.success(data=scheduler.get_all_backends(db))

@router.get("/v1/{app_id}/backends/all")
async def list_app_backends(
    app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """List all backends for a specific app_id"""
    result = scheduler.get_all_app_backends(db, app_id)
    if result:
        return APIResponse.success(data=result)
    return APIResponse.error(f"No backends found for app_id={app_id}")

@router.get("/v1/{app_id}/backends")
async def get_backends(
    app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Get backends for a specific app_id filtered by policy"""
    result = scheduler.get_app_backends(db, app_id)
    if result:
        return APIResponse.success(data=result)
    return APIResponse.error(f"No backends found for app_id={app_id}")

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
async def update_backend_state(
    app_id: str,
    backend_id: str,
    state: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update backend state (active/down)"""
    try:
        logger.debug(f"Updating backend state for app_id={app_id}, backend_id={backend_id} to {state}")
        scheduler.update_backend_state(db, app_id, backend_id, state)
        return APIResponse.success(msg=f"Backend state updated to {state}")
    except Exception as e:
        return APIResponse.error(str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}/{new_app_id}")
async def update_backend_app(
    app_id: str,
    backend_id: str,
    new_app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update the app_id of a backend"""
    try:
        scheduler.update_backend_app_id(db, app_id, backend_id, new_app_id)
        return APIResponse.success(msg=f"Backend app_id updated to {new_app_id}")
    except Exception as e:
        return APIResponse.error(str(e))

@router.patch("/v1/{app_id}/backends/{backend_id}/{weight}")
async def update_backend_weight(
    app_id: str,
    backend_id: str,
    weight: int,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update backend weight for load balancing"""
    try:
        scheduler.update_backend_weight(db, app_id, backend_id, weight)
        return APIResponse.success(msg=f"Backend weight updated to {weight}")
    except Exception as e:
        return APIResponse.error(str(e))

# Policy Management APIs
@router.get("/v1/policies")
async def list_policies() -> APIResponse:
    """List all supported policies"""
    return APIResponse.success(data=scheduler.get_all_policies())

@router.get("/v1/{app_id}/policy")
async def get_policy(
    app_id: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Get the policy of an app"""
    try:
        return APIResponse.success(data=scheduler.get_policy(db, app_id))
    except Exception as e:
        return APIResponse.error(str(e))

@router.patch("/v1/{app_id}/policy")
async def update_policy(
    app_id: str,
    policy: Policy,
    db: Session = Depends(get_db)
) -> APIResponse:
    """Update the policy of a backend selection policy"""
    try:    
        scheduler.update_policy(db, app_id, policy)
        return APIResponse.success(msg=f"{app_id}'s policy now is {policy.policy_type}, limit: {policy.limit}")
    except Exception as e:
        return APIResponse.error(str(e))
