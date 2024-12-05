from abc import ABC, abstractmethod
from typing import List, Optional
import random
from .database import BackendDB

class BackendPolicy(ABC):
    """Abstract base class for backend selection policies"""
    # Default limit to 1 to avoid empty selection
    def __init__(self, limit: Optional[int] = 1):
        self.limit = limit
    
    @abstractmethod
    def select_backends(self, backends: List[BackendDB]) -> List[BackendDB]:
        """Select backends according to the policy"""
        pass
    
    def _apply_limit(self, backends: List[BackendDB]) -> List[BackendDB]:
        """Apply limit to selected backends"""
        if self.limit is not None and len(backends) > self.limit:
            return backends[:self.limit]
        return backends
        
    def update_limit(self, new_limit: int) -> None:
        """Update the policy's limit
        
        Args:
            new_limit (int): New limit value, must be greater than 0
            
        Raises:
            ValueError: If new_limit is less than 1
        """
        if new_limit < 1:
            raise ValueError("Limit must be greater than 0")
        self.limit = new_limit

class RoundRobinPolicy(BackendPolicy):
    """Round-robin backend selection policy"""
    def __init__(self, limit: Optional[int] = 1):
        super().__init__(limit)
        self._current_index = 0
    
    def select_backends(self, backends: List[BackendDB]) -> List[BackendDB]:
        if not backends:
            return []
        
        active_backends = [b for b in backends if b.status == "active"]
        if not active_backends:
            return []
            
        # Calculate and apply the limit
        self.limit = min(self.limit or 1, len(active_backends))

        # Get view from current index to end + wrap around
        backends_view = active_backends[self._current_index:] + active_backends[:self._current_index]

        # Update current index for next call
        self._current_index = (self._current_index + self.limit) % len(active_backends)
        
        # Apply limit to the current index
        return self._apply_limit(backends_view)

class WeightedPolicy(BackendPolicy):
    """Weight-based backend selection policy"""
    def __init__(self, limit: Optional[int] = 3):
        super().__init__(limit)
    
    def select_backends(self, backends: List[BackendDB]) -> List[BackendDB]:
        active_backends = [b for b in backends if b.status == "active"]
        if not active_backends:
            return []
            
        # Sort by weight in descending order
        sorted_backends = sorted(active_backends, key=lambda x: x.weight, reverse=True)
        return self._apply_limit(sorted_backends)

class AllActivePolicy(BackendPolicy):
    """Return all active backends"""
    def select_backends(self, backends: List[BackendDB]) -> List[BackendDB]:
        active_backends = [b for b in backends if b.status == "active"]
        return self._apply_limit(active_backends)

class RandomPolicy(BackendPolicy):
    """Random backend selection policy"""
    def __init__(self, limit: Optional[int] = 1):
        super().__init__(limit)
    
    def select_backends(self, backends: List[BackendDB]) -> List[BackendDB]:
        active_backends = [b for b in backends if b.status == "active"]
        if not active_backends:
            return []
            
        # Randomly shuffle the active backends
        shuffled = list(active_backends)
        random.shuffle(shuffled)
        return self._apply_limit(shuffled) 