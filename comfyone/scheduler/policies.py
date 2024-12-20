from abc import ABC, abstractmethod
from typing import List, Optional
import random
from .models import Backend, PolicyType

class BackendPolicy(ABC):
    """Abstract base class for backend selection policies"""
    # Default limit to 1 to avoid empty selection
    def __init__(self, limit: Optional[int] = 1):
        self.limit = limit
    
    def update_limit(self, new_limit: int) -> None:
        self.limit = new_limit
    
    @abstractmethod
    def select_backends(self, backends: List[Backend]) -> List[Backend]:
        """Select backends according to the policy"""
        pass

    @abstractmethod
    def short_name(self) -> str:
        """Short name of the policy"""
        pass
    
    def _apply_limit(self, backends: List[Backend]) -> List[Backend]:
        """Apply limit to selected backends"""
        if self.limit is not None and len(backends) > self.limit:
            return backends[:self.limit]
        return backends
        

class RoundRobinPolicy(BackendPolicy):
    """Round-robin backend selection policy"""
    def __init__(self, limit: Optional[int] = 1):
        super().__init__(limit)
        self._current_index = 0
    
    def select_backends(self, backends: List[Backend]) -> List[Backend]:
        if not backends:
            return []
        
        active_backends = [b for b in backends if b.state == "active"]
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

    def short_name(self) -> str:
        return "round_robin"

class WeightedPolicy(BackendPolicy):
    """Weight-based backend selection policy"""
    def __init__(self, limit: Optional[int] = 3):
        super().__init__(limit)
    
    def select_backends(self, backends: List[Backend]) -> List[Backend]:
        active_backends = [b for b in backends if b.state == "active"]
        if not active_backends:
            return []
            
        # Sort by weight in descending order
        sorted_backends = sorted(active_backends, key=lambda x: x.weight, reverse=True)
        return self._apply_limit(sorted_backends)

    def short_name(self) -> str:
        return "weighted"

class AllActivePolicy(BackendPolicy):
    """Return all active backends"""
    def select_backends(self, backends: List[Backend]) -> List[Backend]:
        active_backends = [b for b in backends if b.state == "active"]
        return self._apply_limit(active_backends)

    def short_name(self) -> str:
        return "all_active"


class RandomPolicy(BackendPolicy):
    """Random backend selection policy"""
    def __init__(self, limit: Optional[int] = 1):
        super().__init__(limit)
    
    def select_backends(self, backends: List[Backend]) -> List[Backend]:
        active_backends = [b for b in backends if b.state == "active"]
        if not active_backends:
            return []
            
        # Randomly shuffle the active backends
        shuffled = list(active_backends)
        random.shuffle(shuffled)
        return self._apply_limit(shuffled) 

    def short_name(self) -> str:
        return "random"

def create_policy(policy_type: PolicyType, limit: Optional[int] = None) -> BackendPolicy:
    """
    Factory function to create a policy instance based on type and limit
    
    Args:
        policy_type: Type of policy to create
        limit: Optional limit for the policy (uses default if None)
    
    Returns:
        BackendPolicy: Instance of the requested policy
    """
    policy_classes = {
        PolicyType.ROUND_ROBIN: RoundRobinPolicy,
        PolicyType.WEIGHTED: WeightedPolicy,
        PolicyType.ALL_ACTIVE: AllActivePolicy,
        PolicyType.RANDOM: RandomPolicy
    }
    
    policy_class = policy_classes.get(policy_type)
    if not policy_class:
        raise ValueError(f"Unknown policy type: {policy_type}")
        
    return policy_class(limit=limit)
