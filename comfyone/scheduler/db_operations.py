from typing import List
from sqlalchemy.orm import Session
from .database import BackendDB, PolicyDB
from .models import Backend, Policy, PolicyType

class DBOperations:
    @staticmethod
    def add_backend(db: Session, backend: Backend) -> Backend:
        """Add a new backend to the database"""
        # Check if instance_id already exists
        existing_backend = db.query(BackendDB).filter(BackendDB.instance_id == backend.instance_id).first()
        if existing_backend:
            raise ValueError(f"Backend with {backend.instance_id} already exists")
        
        db_backend = BackendDB(
            app_id=backend.app_id,
            instance_id=backend.instance_id,
            weight=backend.weight,
            state=backend.state
        )
        db.add(db_backend)
        db.commit()
        db.refresh(db_backend)
        db.expire_all()
        
        return Backend.from_orm(db_backend)

    @staticmethod
    def get_all_backends(db: Session) -> List[Backend]:
        """Get all backends from database"""
        backends = db.query(BackendDB).all()
        return [Backend.from_orm(b) for b in backends]

    @staticmethod
    def get_app_backends(db: Session, app_id: str) -> List[Backend]:
        """Get all backends for a specific app_id"""
        backends = db.query(BackendDB).filter(BackendDB.app_id == app_id).all()
        return [Backend.from_orm(b) for b in backends]

    @staticmethod
    def remove_backend(db: Session, app_id: str, backend_id: str) -> Backend:
        """Remove a backend from database"""
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == app_id,
            BackendDB.instance_id == backend_id
        ).first()
        if not backend:
            raise ValueError("Backend not found")
        
        db.delete(backend)
        db.commit()
        db.expire_all()
        
        return Backend.from_orm(backend)

    @staticmethod
    def update_backend_state(db: Session, app_id: str, backend_id: str, state: str) -> Backend:
        """Update backend state in database"""
        if state not in ["active", "down"]:
            raise ValueError("State must be either 'active' or 'down'")
        
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == app_id,
            BackendDB.instance_id == backend_id
        ).first()
        
        if not backend:
            raise ValueError("Backend not found")
        
        backend.state = state
        db.commit()
        db.refresh(backend)
        db.expire_all()
        
        return Backend.from_orm(backend)

    @staticmethod
    def update_backend_app_id(db: Session, current_app_id: str, backend_id: str, new_app_id: str) -> Backend:
        """Update backend app_id in database"""
        if not new_app_id:
            raise ValueError("New app_id cannot be empty")
        
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == current_app_id,
            BackendDB.instance_id == backend_id
        ).first()
        
        if not backend:
            raise ValueError("Backend not found")
        
        backend.app_id = new_app_id
        db.commit()
        db.refresh(backend)
        db.expire_all()
        
        return Backend.from_orm(backend)

    @staticmethod
    def update_backend_weight(db: Session, app_id: str, backend_id: str, weight: int) -> Backend:
        """Update backend weight in database"""
        if weight < 1:
            raise ValueError("Weight must be greater than 0")
            
        backend = db.query(BackendDB).filter(
            BackendDB.app_id == app_id,
            BackendDB.instance_id == backend_id
        ).first()
        
        if not backend:
            raise ValueError("Backend not found")
        
        backend.weight = weight
        db.commit()
        db.refresh(backend)
        db.expire_all()
        
        return Backend.from_orm(backend) 
    
    @staticmethod
    def add_or_update_policy(db: Session, app_id: str, policy: Policy) -> Policy:
        """Add a new policy to the database if it doesn't exist, otherwise update it"""
        db_policy = db.query(PolicyDB).filter(PolicyDB.app_id == app_id).first()
        if not db_policy:
            db_policy = PolicyDB(
                app_id=app_id,
                policy_type=policy.policy_type,
                limit=policy.limit
            )
            db.add(db_policy)
        else:
            db_policy.policy_type = policy.policy_type
            db_policy.limit = policy.limit
            
        db.commit()
        db.refresh(db_policy)
        db.expire_all()
        return Policy.from_orm(db_policy)

    @staticmethod
    def remove_policy(db: Session, app_id: str) -> Policy:
        """Remove policy from database"""
        db_policy = db.query(PolicyDB).filter(PolicyDB.app_id == app_id).first()
        if not db_policy:
            raise ValueError(f"Policy of {app_id} not found")
        
        db.delete(db_policy)
        db.commit()
        db.expire_all()
        return Policy.from_orm(db_policy)
    
    @staticmethod  
    def update_policy(db: Session, app_id: str, policy: Policy) -> Policy:
        """Update policy type in database"""
        db_policy = db.query(PolicyDB).filter(PolicyDB.app_id == app_id).first()
        if not db_policy:
            raise ValueError(f"Policy of {app_id} not found")
        
        db_policy.policy_type = policy.policy_type
        db_policy.limit = policy.limit
        db.commit()
        db.refresh(db_policy)
        db.expire_all()
        return Policy.from_orm(db_policy)

    @staticmethod
    def get_policy(db: Session, app_id: str) -> Policy:
        """Get policy for a specific app_id"""
        db_policy = db.query(PolicyDB).filter(PolicyDB.app_id == app_id).first()
        if not db_policy:
            raise ValueError(f"Policy of {app_id} not found")
        return Policy.from_orm(db_policy)
    
    @staticmethod
    def update_policy_limit(db: Session, app_id: str, policy: Policy) -> Policy:
        """Update policy limit in database"""
        db_policy = db.query(PolicyDB).filter(
            PolicyDB.app_id == app_id,
            PolicyDB.policy_type == policy.policy_type
        ).first()
        
        if not db_policy:
            raise ValueError(f"Policy of {app_id} not found")
        
        db_policy.limit = policy.limit
        db.commit()
        db.refresh(db_policy)
        db.expire_all()
        
        return Policy.from_orm(db_policy)
