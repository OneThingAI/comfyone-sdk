import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import pytest
import requests
import logging
from comfyone.scheduler.models import Backend, Policy, PolicyType

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

@pytest.fixture
def sample_backend():
    return Backend(
        app_id="test-app",
        instance_id="instance-1",
        weight=1,
        state="active"
    ).model_dump()

class TestSchedulerAPI:
    def test_add_backend(self, sample_backend):
        response = requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        assert response.status_code == 200
        data = response.json()
        logger.info(f"Add backend response: {data}")
        assert data["code"] == 0
        assert data["msg"] == "Backend added successfully"
        assert data["data"]["backend"]["instance_id"] == sample_backend["instance_id"]
        assert data["data"]["policy"] is not None

    def test_get_backends_no_policy(self, sample_backend):
        # First add a backend
        response = requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        logger.info(f"Add backend response: {response.json()}")
        
        # Then get backends without policy
        response = requests.get(f"{BASE_URL}/v1/{sample_backend['app_id']}/backends")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1
        assert data["data"][0]["instance_id"] == sample_backend["instance_id"]

    def test_list_all_backends(self, sample_backend):
        # First add a backend
        requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        
        # Then list all backends
        response = requests.get(f"{BASE_URL}/v1/backends/all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) >= 1

    def test_list_app_backends(self, sample_backend):
        # First add a backend
        requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        
        # Then list app backends
        response = requests.get(f"{BASE_URL}/v1/{sample_backend['app_id']}/backends/all")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) >= 1

    def test_list_policies(self):
        response = requests.get(f"{BASE_URL}/v1/policies")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        policies = data["data"]
        assert len(policies) == 4  # Should have 4 default policies
        policy_types = [p["type"] for p in policies]
        assert PolicyType.ROUND_ROBIN.value in policy_types
        assert PolicyType.WEIGHTED.value in policy_types
        assert PolicyType.ALL_ACTIVE.value in policy_types
        assert PolicyType.RANDOM.value in policy_types

    def test_update_policy(self, sample_backend):
        policy = Policy(
            app_id=sample_backend["app_id"],
            policy_type=PolicyType.ROUND_ROBIN,
            limit=2
        )
        response = requests.patch(
            f"{BASE_URL}/v1/{sample_backend['app_id']}/policy",
            json=policy.model_dump()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["limit"] == 2

    def test_update_backend_state(self, sample_backend):
        # First add a backend
        requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        
        # Then update its state
        response = requests.patch(
            f"{BASE_URL}/v1/{sample_backend['app_id']}/backends/{sample_backend['instance_id']}",
            params={"state": "down"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "Backend state updated to down" in data["msg"]

    def test_update_backend_app_id(self, sample_backend):
        # First add a backend
        requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        
        new_app_id = "new-test-app"
        response = requests.patch(
            f"{BASE_URL}/v1/{sample_backend['app_id']}/backends/{sample_backend['instance_id']}/{new_app_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert f"Backend app_id updated to {new_app_id}" in data["msg"]

    def test_update_backend_weight(self, sample_backend):
        # First add a backend
        requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        
        new_weight = 5
        response = requests.patch(
            f"{BASE_URL}/v1/{sample_backend['app_id']}/backends/{sample_backend['instance_id']}/{new_weight}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert f"Backend weight updated to {new_weight}" in data["msg"]

    def test_remove_backend(self, sample_backend):
        # First add a backend
        requests.post(f"{BASE_URL}/v1/backends", json=sample_backend)
        
        # Then remove it
        response = requests.delete(
            f"{BASE_URL}/v1/{sample_backend['app_id']}/backends/{sample_backend['instance_id']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "Backend removed successfully"

        # Verify it's gone
        response = requests.get(f"{BASE_URL}/v1/{sample_backend['app_id']}/backends")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert len(data["data"]) == 0