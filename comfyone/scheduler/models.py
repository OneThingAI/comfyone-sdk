from typing import Optional, Any, TypeVar, Generic
from pydantic import BaseModel

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
    def error(cls, msg: str = "error", data: Optional[T] = None) -> "APIResponse[T]":
        """Create an error response"""
        return cls(
            code=1,
            msg=msg,
            data=data
        ) 