import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from comfyone.scheduler.database import Base
from comfyone.scheduler.main import app
from comfyone.scheduler.backend_scheduler import get_db
from comfyone.scheduler.models import Backend, PolicyType

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def sample_backend():
    return {
        "name": "test_backend",
        "host": "instance-1",
        "weight": 1,
        "state": "active"
    }

class TestSchedulerAPI:
    def test_add_backend(self, sample_backend):
        response = client.post("/v1/test-app/backends", json=sample_backend)
        assert response.status_code == 200
        data = response.json()
        print(f"Add backend response: {data}")
        assert data["code"] == 0
        assert data["msg"] == "Backend added successfully"
        assert data["data"]["name"] == sample_backend["name"]
        assert data["data"]["host"] == sample_backend["host"]

    def test_get_backends_no_policy(self, sample_backend):
        # First add a backend
        client.post("/v1/test-app/backends", json=sample_backend)
        
        # Then get backends without policy
        response = client.get("/v1/test-app/backends")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == sample_backend["name"]

    def test_get_backends_with_policy(self, sample_backend):
        # First add a backend
        client.post("/v1/test-app/backends", json=sample_backend)
        
        # Then get backends with round_robin policy
        response = client.get("/v1/test-app/backends?policy=round_robin")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1

    def test_list_policies(self):
        response = client.get("/v1/policies")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        policies = data["data"]
        assert len(policies) == 4  # Should have 4 default policies
        policy_types = [p["type"] for p in policies]
        assert PolicyType.ROUND_ROBIN in policy_types
        assert PolicyType.WEIGHTED in policy_types
        assert PolicyType.ALL_ACTIVE in policy_types
        assert PolicyType.RANDOM in policy_types

    def test_update_policy_limit(self):
        response = client.patch("/v1/policies/round_robin/limit?new_limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["new_limit"] == 3

    def test_update_backend_state(self, sample_backend):
        # First add a backend
        add_response = client.post("/v1/test-app/backends", json=sample_backend)
        backend_id = add_response.json()["data"]["id"]
        
        # Then update its state
        response = client.patch(f"/v1/test-app/backends/{backend_id}?state=down")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["state"] == "down"

    def test_update_backend_weight(self, sample_backend):
        # First add a backend
        add_response = client.post("/v1/test-app/backends", json=sample_backend)
        backend_id = add_response.json()["data"]["id"]
        
        # Then update its weight
        new_weight = 5
        response = client.patch(f"/v1/test-app/backends/{backend_id}/weight?weight={new_weight}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["weight"] == new_weight

    def test_remove_backend(self, sample_backend):
        # First add a backend
        add_response = client.post("/v1/test-app/backends", json=sample_backend)
        backend_id = add_response.json()["data"]["id"]
        
        # Then remove it
        response = client.delete(f"/v1/test-app/backends/{backend_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "Backend removed successfully"

        # Verify it's gone
        get_response = client.get("/v1/test-app/backends")
        assert len(get_response.json()["data"]) == 0 