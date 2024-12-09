# install test dependencies first
# pip install pytest pytest-mock
# Cursor Generated Unit Test for BackendScheduler, I think it's not working
import sys
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from comfyone.scheduler.backend_scheduler import (
    BackendScheduler, Backend, PolicyType, POLICY_MAP
)
from comfyone.scheduler.models import APIResponse
from comfyone.scheduler.database import BackendDB

@pytest.fixture
def mock_db():
    print("\nSetting up mock database session")
    return Mock(spec=Session)

@pytest.fixture
def scheduler():
    print("\nInitializing BackendScheduler")
    return BackendScheduler()

@pytest.fixture
def sample_backend():
    print("\nCreating sample backend")
    return Backend(
        name="test_backend",
        host="test_host"
    )

@pytest.fixture
def sample_backend_db():
    print("\nCreating sample backend DB entry")
    return BackendDB(
        id="test-id",
        app_id="test-app",
        name="test_backend",
        host="test_host",
        weight=1,
        status="active"
    )

class TestBackendScheduler:
    def test_add_backend_success(self, scheduler, mock_db, sample_backend):
        print("\nTesting add_backend success case")
        # Mock db_ops response
        scheduler.db_ops.add_backend.return_value = APIResponse.success(
            data=sample_backend,
            msg="Backend added successfully"
        )

        result = scheduler.add_backend(mock_db, "test-app", sample_backend)
        print(f"Add backend result: code={result.code}, msg={result.msg}")
        
        assert result.code == 0
        assert result.msg == "Backend added successfully"
        assert result.data == sample_backend
        scheduler.db_ops.add_backend.assert_called_once_with(mock_db, "test-app", sample_backend)

    def test_get_backends_with_policy(self, scheduler, mock_db, sample_backend_db):
        print("\nTesting get_backends with policy")
        # Mock db_ops response
        scheduler.db_ops.get_app_backends.return_value = APIResponse.success(
            data=[sample_backend_db],
            msg="Successfully retrieved backends"
        )

        policy = POLICY_MAP[PolicyType.ROUND_ROBIN]
        print(f"Using policy: {PolicyType.ROUND_ROBIN} with limit {policy.limit}")
        result = scheduler.get_backends(mock_db, "test-app", policy)
        print(f"Get backends result: code={result.code}, backends_count={len(result.data)}")
        
        assert result.code == 0
        assert len(result.data) == 1
        assert result.data[0].name == "test_backend"
        scheduler.db_ops.get_app_backends.assert_called_once_with(mock_db, "test-app")

    def test_get_backends_no_policy(self, scheduler, mock_db, sample_backend_db):
        print("\nTesting get_backends without policy")
        # Mock db_ops response
        scheduler.db_ops.get_app_backends.return_value = APIResponse.success(
            data=[sample_backend_db],
            msg="Successfully retrieved backends"
        )

        result = scheduler.get_backends(mock_db, "test-app")
        print(f"Get backends result: code={result.code}, backends_count={len(result.data)}")
        
        assert result.code == 0
        assert len(result.data) == 1
        assert result.data[0].name == "test_backend"
        scheduler.db_ops.get_app_backends.assert_called_once_with(mock_db, "test-app")

    def test_update_policy_limit_success(self, scheduler):
        print("\nTesting update_policy_limit success case")
        policy_type = PolicyType.ROUND_ROBIN
        new_limit = 2
        
        result = scheduler.update_policy_limit(policy_type, new_limit)
        print(f"Update policy limit result: code={result.code}, new_limit={new_limit}")
        
        assert result.code == 0
        assert result.data["policy"] == policy_type
        assert result.data["new_limit"] == new_limit
        assert POLICY_MAP[policy_type].limit == new_limit

    def test_update_policy_limit_invalid_policy(self, scheduler):
        print("\nTesting update_policy_limit with invalid policy")
        result = scheduler.update_policy_limit("invalid_policy", 2)
        print(f"Update invalid policy result: code={result.code}, msg={result.msg}")
        
        assert result.code == 1
        assert result.msg == "Policy not found"

    def test_get_supported_policies(self, scheduler):
        print("\nTesting get_supported_policies")
        result = scheduler.get_supported_policies()
        print(f"Get policies result: code={result.code}, policies_count={len(result.data)}")
        
        assert result.code == 0
        assert len(result.data) == len(POLICY_MAP)
        for policy_info in result.data:
            assert "type" in policy_info
            assert "limit" in policy_info
            assert "description" in policy_info

    @pytest.mark.parametrize("policy_type,expected_limit", [
        (PolicyType.ROUND_ROBIN, 1),
        (PolicyType.WEIGHTED, 3),
        (PolicyType.ALL_ACTIVE, 5),
        (PolicyType.RANDOM, 1)
    ])
    def test_policy_default_limits(self, policy_type, expected_limit):
        print(f"\nTesting default limit for policy: {policy_type}")
        policy = POLICY_MAP[policy_type]
        print(f"Policy {policy_type} has limit: {policy.limit}")
        assert policy.limit == expected_limit

    def test_backend_validation(self):
        print("\nTesting backend validation")
        # Test valid backend
        backend = Backend(name="test", host="test_host")
        print(f"Valid backend created with state={backend.state}, weight={backend.weight}")
        assert backend.state == "active"
        assert backend.weight == 1

        # Test invalid state
        print("Testing invalid state validation")
        with pytest.raises(ValueError):
            Backend(name="test", host="test_host", state="invalid")