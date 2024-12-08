import logging
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from .models import Backend, PolicyType, Policy, POLICY_MAPPER
from .db_operations import DBOperations
from .policies import BackendPolicy, RoundRobinPolicy, WeightedPolicy, AllActivePolicy, RandomPolicy:w


logger = logging.getLogger("scheduler")

class BackendScheduler:
    def __init__(self):
        self.default_policy = Policy(policy_type=PolicyType.ROUND_ROBIN, limit=1)
        self.db_ops = DBOperations()
        logger.debug(f"Initialized BackendScheduler with default policy: {self.default_policy.policy_type}")
    
    def add_backend(self, db: Session, backend: Backend) -> Tuple[Backend, Policy]:
        logger.debug(f"Adding backend: {backend}")
        try:
            backend_ret = self.db_ops.add_backend(db, backend)
        except ValueError as e:
            logger.error(f"Failed to add backend: {str(e)}")
            raise ValueError(str(e))
        try:
            policy_ret = self.db_ops.get_policy(db, backend.app_id)
        except ValueError as e:
            logger.error(f"Failed to get policy: {str(e)}")
            # if policy not found, add default policy for the app
            policy_ret = self.db_ops.add_or_update_policy(db, backend.app_id, self.default_policy)
        return backend_ret, policy_ret

    def get_all_backends(self, db: Session) -> List[Backend]:
        return self.db_ops.get_all_backends(db)

    # return all backends for a specific app_id, if not found, return empty list
    def get_all_app_backends(self, db: Session, app_id: str) -> List[Backend]:
        return self.db_ops.get_app_backends(db, app_id)

    def get_app_backends(self, db: Session, app_id: str) -> List[Backend]:
        """Get backends filtered by policy"""
        try:
            logger.info(f"Getting backends for app_id={app_id}")
            try:
                policy = self.db_ops.get_policy(db, app_id)
            except ValueError as e:
                logger.error(f"Failed to get policy: {str(e)}, using default policy")
                policy = self.default_policy
            
            backends = self.db_ops.get_app_backends(db, app_id)
            selected_policy = POLICY_MAPPER[policy.policy_type].update_limit(policy.limit)
            selected_backends = selected_policy.select_backends(backends)
            logger.debug(f"Selected backends: {[b.instance_id for b in selected_backends]}")
            return selected_backends
        except Exception as e:
            logger.error(f"Error getting backends: {str(e)}")
            return []

    def remove_backend(self, db: Session, app_id: str, backend_id: str) -> Backend:
        return self.db_ops.remove_backend(db, app_id, backend_id)

    def update_backend_state(self, db: Session, app_id: str, backend_id: str, state: str) -> Backend:
        return self.db_ops.update_backend_state(db, app_id, backend_id, state)

    def update_backend_app_id(self, db: Session, current_app_id: str, backend_id: str, new_app_id: str) -> Backend:
        return self.db_ops.update_backend_app_id(db, current_app_id, backend_id, new_app_id)

    def update_backend_weight(self, db: Session, app_id: str, backend_id: str, weight: int) -> Backend:
        return self.db_ops.update_backend_weight(db, app_id, backend_id, weight)

    def update_policy(self, db: Session, app_id: str, policy: Policy) -> Policy:
        """Update policy type in database"""
        return self.db_ops.update_policy(db, app_id, policy)
 
    def update_policy_limit(self, db: Session, app_id: str, policy: Policy) -> Policy:
        """Update the limit of a specific policy"""
        return self.db_ops.update_policy_limit(db, app_id, policy)

    def get_all_policies(self, db: Session) -> List[str]:
        """Get all supported policies"""
        policies = []
        for policy_type in PolicyType:
            policies.append(policy_type)
        return policies

