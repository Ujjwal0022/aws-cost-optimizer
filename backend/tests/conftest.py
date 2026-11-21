"""
conftest.py — Shared pytest fixtures for all tests
Mocks AWS APIs so no real AWS calls are made in tests.
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test.db"

# Patch DATABASE_URL before importing app
import os
os.environ.setdefault("DATABASE_URL",            TEST_DATABASE_URL)
os.environ.setdefault("COGNITO_USER_POOL_ID",    "us-east-1_TEST")
os.environ.setdefault("COGNITO_CLIENT_ID",       "test-client-id")
os.environ.setdefault("COGNITO_CLIENT_SECRET",   "test-client-secret")
os.environ.setdefault("AWS_REGION",              "us-east-1")
os.environ.setdefault("ANTHROPIC_API_KEY",       "test-key")

from app.database.database import Base, get_db
from app.database.models import User, AWSAccount, AuditLog
from app.main import app

# ── Test DB engine ────────────────────────────────────────────────────────────
engine        = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Fresh DB session per test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """FastAPI test client with DB override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Sample data fixtures ──────────────────────────────────────────────────────
@pytest.fixture
def test_user(db):
    user = User(
        cognito_sub="test-cognito-sub-123",
        email="test@example.com",
        full_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_account(db, test_user):
    account = AWSAccount(
        user_id=test_user.id,
        account_name="Test Account",
        aws_account_id="123456789012",
        role_arn="arn:aws:iam::123456789012:role/FinOpsReadOnlyRole",
        external_id="finops-test-external-id",
        default_region="us-east-1",
        connection_status="connected",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def auth_headers():
    """Mock JWT token headers."""
    return {"Authorization": "Bearer mock-test-token"}


@pytest.fixture
def mock_current_user(test_user):
    """Mock the get_current_user dependency."""
    return {
        "user_id": test_user.cognito_sub,
        "email":   test_user.email,
        "name":    test_user.full_name,
        "token":   "mock-test-token",
    }


# ── AWS Mock fixtures ─────────────────────────────────────────────────────────
@pytest.fixture
def mock_sts():
    """Mock STS AssumeRole — no real AWS calls."""
    with patch("boto3.client") as mock_boto:
        sts_client = MagicMock()
        sts_client.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId":     "ASIA_TEST_KEY",
                "SecretAccessKey": "test-secret",
                "SessionToken":    "test-token",
                "Expiration":      "2099-01-01T00:00:00Z",
            }
        }
        sts_client.get_caller_identity.return_value = {
            "Account": "123456789012",
            "UserId":  "AIDTEST123",
            "Arn":     "arn:aws:iam::123456789012:role/FinOpsReadOnlyRole",
        }
        mock_boto.return_value = sts_client
        yield sts_client


@pytest.fixture
def mock_ec2():
    """Mock EC2 describe_instances."""
    with patch("boto3.Session") as mock_session:
        ec2_client = MagicMock()
        ec2_client.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId":   "i-0abc123",
                    "InstanceType": "t3.medium",
                    "State":        {"Name": "running"},
                    "Tags":         [{"Key": "Name", "Value": "test-instance"}],
                    "LaunchTime":   "2024-01-01T00:00:00Z",
                    "Placement":    {"AvailabilityZone": "us-east-1a"},
                    "PublicIpAddress":  "1.2.3.4",
                    "PrivateIpAddress": "10.0.0.1",
                }]
            }]
        }
        ec2_client.describe_volumes.return_value = {
            "Volumes": [{
                "VolumeId":   "vol-0abc123",
                "Size":       20,
                "VolumeType": "gp2",
                "State":      "available",
                "CreateTime": "2024-01-01T00:00:00Z",
            }]
        }
        ec2_client.describe_addresses.return_value = {
            "Addresses": [{
                "AllocationId": "eipalloc-0abc123",
                "PublicIp":     "52.1.2.3",
            }]
        }
        mock_session.return_value.client.return_value = ec2_client
        yield ec2_client


@pytest.fixture
def mock_cost_explorer():
    """Mock AWS Cost Explorer."""
    with patch("boto3.Session") as mock_session:
        ce_client = MagicMock()
        ce_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [{
                "TimePeriod": {"Start": "2024-01-01", "End": "2024-01-31"},
                "Total":      {"UnblendedCost": {"Amount": "450.00", "Unit": "USD"}},
                "Groups":     [],
            }]
        }
        mock_session.return_value.client.return_value = ce_client
        yield ce_client
