from abc import ABC, abstractmethod
from typing import List, Optional
import random
from .database import BackendDB

class BackendPolicy(ABC):
    """Abstract base class for backend selection policies"""
    
    def __init__(self, limit: Optional[int] = None):
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
            
        selected = active_backends[self._current_index % len(active_backends)]
        self._current_index += 1
        return self._apply_limit([selected])

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