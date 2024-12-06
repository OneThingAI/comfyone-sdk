from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./backends.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class BackendDB(Base):
    __tablename__ = "backends"

    id = Column(String, primary_key=True, index=True)
    app_id = Column(String, index=True)
    name = Column(String)
    host = Column(String, unique=True)
    weight = Column(Integer, default=1)
    state = Column(String, default="active")

# Create tables
Base.metadata.create_all(bind=engine) 