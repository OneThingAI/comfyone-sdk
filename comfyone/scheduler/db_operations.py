from typing import List, Optional
from sqlalchemy.orm import Session
from .database import BackendDB
from .models import APIResponse, Backend

class DBOperations:
    @staticmethod
    def add_backend(db: Session, app_id: str, backend: Backend) -> APIResponse:
        """Add a new backend to the database"""
        try:
            # Check if host already exists
            existing_backend = db.query(BackendDB).filter(BackendDB.host == backend.host).first()
            if existing_backend:
                return APIResponse.error("Backend with this host already exists")
            
            db_backend = BackendDB(
                id=backend.id,
                app_id=app_id,
                name=backend.name,
                host=backend.host,
                weight=backend.weight,
                state=backend.state
            )
            db.add(db_backend)
            db.commit()
            db.refresh(db_backend)
            db.expire_all()
            
            return APIResponse.success(
                data=Backend.from_orm(db_backend),
                msg="Backend added successfully"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    @staticmethod
    def get_all_backends(db: Session) -> APIResponse:
        """Get all backends from database"""
        try:
            backends = db.query(BackendDB).all()
            print(backends)
            return APIResponse.success(
                data=[Backend.from_orm(b) for b in backends],
                msg="Successfully retrieved all backends"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    @staticmethod
    def get_app_backends(db: Session, app_id: str) -> APIResponse:
        """Get all backends for a specific app_id"""
        try:
            backends = db.query(BackendDB).filter(BackendDB.app_id == app_id).all()
            return APIResponse.success(
                data=[Backend.from_orm(b) for b in backends],
                msg=f"Successfully retrieved backends for app_id: {app_id}"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    @staticmethod
    def remove_backend(db: Session, app_id: str, backend_id: str) -> APIResponse:
        """Remove a backend from database"""
        try:
            backend = db.query(BackendDB).filter(
                BackendDB.app_id == app_id,
                BackendDB.id == backend_id
            ).first()
            if not backend:
                return APIResponse.error("Backend not found")
            
            db.delete(backend)
            db.commit()
            db.expire_all()
            return APIResponse.success(msg="Backend removed successfully")
        except Exception as e:
            return APIResponse.error(str(e))

    @staticmethod
    def update_backend_state(db: Session, app_id: str, backend_id: str, state: str) -> APIResponse:
        """Update backend state in database"""
        try:
            if state not in ["active", "down"]:
                return APIResponse.error("State must be either 'active' or 'down'")
            
            backend = db.query(BackendDB).filter(
                BackendDB.app_id == app_id,
                BackendDB.id == backend_id
            ).first()
            
            if not backend:
                return APIResponse.error("Backend not found")
            
            backend.state = state
            db.commit()
            db.refresh(backend)
            db.expire_all()
            
            return APIResponse.success(
                data=Backend.from_orm(backend),
                msg=f"Backend state updated to {state}"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    @staticmethod
    def update_backend_app_id(db: Session, current_app_id: str, backend_id: str, new_app_id: str) -> APIResponse:
        """Update backend app_id in database"""
        try:
            if not new_app_id:
                return APIResponse.error("New app_id cannot be empty")
            
            backend = db.query(BackendDB).filter(
                BackendDB.app_id == current_app_id,
                BackendDB.id == backend_id
            ).first()
            
            if not backend:
                return APIResponse.error("Backend not found")
            
            backend.app_id = new_app_id
            db.commit()
            db.refresh(backend)
            db.expire_all()
            
            return APIResponse.success(
                data=Backend.from_orm(backend),
                msg=f"Backend app_id updated to {new_app_id}"
            )
        except Exception as e:
            return APIResponse.error(str(e))

    @staticmethod
    def update_backend_weight(db: Session, app_id: str, backend_id: str, weight: int) -> APIResponse:
        """Update backend weight in database"""
        try:
            if weight < 1:
                return APIResponse.error("Weight must be greater than 0")
                
            backend = db.query(BackendDB).filter(
                BackendDB.app_id == app_id,
                BackendDB.id == backend_id
            ).first()
            
            if not backend:
                return APIResponse.error("Backend not found")
            
            backend.weight = weight
            db.commit()
            db.refresh(backend)
            db.expire_all()
            
            return APIResponse.success(
                data=Backend.from_orm(backend),
                msg=f"Backend weight updated to {weight}"
            )
        except Exception as e:
            return APIResponse.error(str(e)) 