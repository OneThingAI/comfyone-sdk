from typing import Optional, TypeVar, Generic, Literal, Dict
from pydantic import BaseModel, validator
import uuid
from enum import Enum

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response structure"""
    code: int = 0  # 0 for success, 1 for failure
    msg: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Optional[T] = None, msg: str = "success") -> "APIResponse[T]":
        """Create a success response"""
        return cls(
            code=0,
            msg=msg,
            data=data
        )
    
    @classmethod
    def error(cls, msg: str) -> "APIResponse[T]":
        """Create an error response"""
        return cls(
            code=1,
            msg=msg,
            data=None
        )

class Backend(BaseModel):
    id: str = str(uuid.uuid4())
    app_id: str
    instance_id: str
    weight: Optional[int] = 1
    state: str = "active"

    @validator('state')
    def validate_state(cls, v):
        if v not in ["active", "down"]:
            raise ValueError("State must be either 'active' or 'down'")
        return v

    model_config = {
        "from_attributes": True
    }


class PolicyType(str, Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    ALL_ACTIVE = "all_active"
    RANDOM = "random"


class Policy(BaseModel):
    policy_type: PolicyType
    limit: int = 1

    model_config = {
        "from_attributes": True
    }


