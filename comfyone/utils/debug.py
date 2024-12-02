import time
import contextlib
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DebugContext:
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    context: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "context": self.context
        }

@contextlib.contextmanager
def debug_context(logger, operation: str, **kwargs):
    """Context manager for debugging operations"""
    ctx = DebugContext(context=kwargs)
    logger.debug(f"Starting {operation}", extra={"debug_context": ctx.to_dict()})
    
    try:
        yield ctx
    except Exception as e:
        ctx.end_time = datetime.now()
        ctx.duration = (ctx.end_time - ctx.start_time).total_seconds()
        ctx.context["error"] = str(e)
        logger.error(
            f"Error in {operation}: {e}",
            extra={"debug_context": ctx.to_dict()},
            exc_info=True
        )
        raise
    else:
        ctx.end_time = datetime.now()
        ctx.duration = (ctx.end_time - ctx.start_time).total_seconds()
        logger.debug(
            f"Completed {operation}",
            extra={"debug_context": ctx.to_dict()}
        ) 