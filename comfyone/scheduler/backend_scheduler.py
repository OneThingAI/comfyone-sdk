from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from .database import SessionLocal, BackendDB
from .policies import BackendPolicy, RoundRobinPolicy
from enum import Enum
from .models import APIResponse, Backend, PolicyType, POLICY_MAP
from .db_operations import DBOperations
import logging
from pydantic import ValidationError

router = APIRouter()

logger = None

def setup_external_logger(external_logger: logging.Logger = None):
    """Initialize scheduler with optional external logger"""
    global logger
    if external_logger:
        logger = external_logger
        logger.debug("External logger configured for backend scheduler")

def _log_debug(msg: str):
    """Internal helper to safely log debug messages"""
    if logger:
        logger.debug(msg)

def _log_error(msg: str):
    """Internal helper to safely log error messages"""
    if logger:
        logger.error(msg)

def _log_info(msg: str):
    """Internal helper to safely log info messages"""
    if logger:
        logger.info(msg)
    
def _log_warning(msg: str):
    """Internal helper to safely log warning messages"""
    if logger:
        logger.warning(msg)

# Dependency to get DB session
def get_db():
    _log_debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        _log_debug("Closing database session")
        db.close()

class BackendScheduler:
    def __init__(self, default_policy: BackendPolicy = None):
        self.default_policy = default_policy or RoundRobinPolicy(limit=1)
        self.db_ops = DBOperations()
        _log_debug(f"Initialized BackendScheduler with default policy: {self.default_policy.__class__.__name__}")
    
    def add_backend(self, db: Session, app_id: str, backend: Backend) -> APIResponse:
        _log_debug(f"Adding backend for app_id={app_id}: {backend}")
        result = self.db_ops.add_backend(db, app_id, backend)
        _log_debug(f"Add backend result: {result}")
        return result

    def get_backends(self, db: Session, app_id: str, policy: BackendPolicy = None) -> APIResponse:
        """Get backends filtered by policy"""
        try:
            _log_debug(f"Getting backends for app_id={app_id} with policy={policy.__class__.__name__ if policy else None}")
            backends_response = self.db_ops.get_app_backends(db, app_id)
            if backends_response.code != 0:
                _log_error(f"Failed to get backends: {backends_response.msg}")
                return backends_response
            
            selected_policy = policy or self.default_policy
            _log_debug(f"Using policy: {selected_policy.__class__.__name__} with limit {selected_policy.limit}")
            selected_backends = selected_policy.select_backends(backends_response.data)
            _log_debug(f"Selected {len(selected_backends)} backends")
            
            return APIResponse.success(
                data=[Backend.from_orm(b) for b in selected_backends],
                msg="Successfully retrieved backends"
            )
        except Exception as e:
            _log_error("Error getting backends")
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
        _log_debug(f"Received backend data: {backend.dict()}")
        result = scheduler.add_backend(db, app_id, backend)
        
        if result.code != 0:
            _log_error(f"Failed to add backend: {result.msg}")
            return result
            
        _log_debug(f"Successfully added backend: {result.data}")
        return APIResponse.success(
            data=result.data,
            msg="Backend added successfully"
        )
    except ValidationError as e:
        _log_error(f"Validation error: {str(e)}")
        return APIResponse.error(f"Validation error: {str(e)}")
    except Exception as e:
        _log_error("Unexpected error while adding backend")
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
    if result.code != 0:
        return result
    return result  # Return the result directly since it's already an APIResponse

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