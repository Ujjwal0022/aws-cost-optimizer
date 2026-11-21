"""
Tests for AWS account management.
Critical: ownership checks prevent IDOR attacks.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.auth.dependencies import get_current_user
from app.main import app


def override_auth(user):
    """Helper to override auth dependency."""
    app.dependency_overrides[get_current_user] = lambda: user
    return user


class TestConnectAccount:
    def test_connect_account_success(self, client, test_user, db):
        mock_user = {
            "user_id": test_user.cognito_sub,
            "email":   test_user.email,
            "token":   "mock-token",
        }
        override_auth(mock_user)

        with patch("app.services.account_service.validate_account_connection") as mock_validate:
            mock_validate.return_value = {
                "valid":      True,
                "account_id": "123456789012",
                "arn":        "arn:aws:iam::123456789012:role/FinOpsReadOnlyRole",
            }

            res = client.post("/accounts/", json={
                "account_name":   "Production",
                "aws_account_id": "123456789012",
                "role_arn":       "arn:aws:iam::123456789012:role/FinOpsReadOnlyRole",
                "default_region": "us-east-1",
            })
            assert res.status_code == 201
            data = res.json()
            assert data["account_name"]   == "Production"
            assert data["aws_account_id"] == "123456789012"
            assert data["connection_status"] == "connected"
            assert "external_id" in data

        app.dependency_overrides.clear()

    def test_connect_duplicate_account(self, client, test_user, test_account):
        mock_user = {"user_id": test_user.cognito_sub, "email": test_user.email, "token": "t"}
        override_auth(mock_user)

        with patch("app.services.account_service.validate_account_connection") as mock_v:
            mock_v.return_value = {"valid": True, "account_id": "123456789012"}

            res = client.post("/accounts/", json={
                "account_name":   "Duplicate",
                "aws_account_id": "123456789012",   # same as test_account
                "role_arn":       "arn:aws:iam::123456789012:role/FinOpsReadOnlyRole",
            })
            assert res.status_code == 400
            assert "already connected" in res.json()["detail"]

        app.dependency_overrides.clear()

    def test_connect_failed_sts(self, client, test_user):
        mock_user = {"user_id": test_user.cognito_sub, "email": test_user.email, "token": "t"}
        override_auth(mock_user)

        with patch("app.services.account_service.validate_account_connection") as mock_v:
            mock_v.return_value = {
                "valid": False,
                "error": "Access denied. Check IAM role trust policy.",
            }

            res = client.post("/accounts/", json={
                "account_name":   "Bad Account",
                "aws_account_id": "999999999999",
                "role_arn":       "arn:aws:iam::999999999999:role/BadRole",
            })
            # Should still create but with failed status
            assert res.status_code == 201
            data = res.json()
            assert data["connection_status"] == "failed"
            assert "warning" in data

        app.dependency_overrides.clear()


class TestAccountOwnership:
    """
    Critical security tests — User A must NEVER access User B's accounts.
    """

    def test_cannot_access_other_users_account(self, client, test_user, test_account, db):
        from app.database.models import User
        # Create User B
        user_b = User(
            cognito_sub="user-b-cognito-sub",
            email="userb@example.com",
            full_name="User B",
        )
        db.add(user_b)
        db.commit()

        # User B tries to access test_account (belongs to test_user)
        mock_user_b = {"user_id": "user-b-cognito-sub", "email": "userb@example.com", "token": "t"}
        override_auth(mock_user_b)

        res = client.get(f"/accounts/{test_account.id}")
        assert res.status_code == 404   # Not found — correct, not 403 to avoid info leak

        app.dependency_overrides.clear()

    def test_list_accounts_only_own(self, client, test_user, test_account, db):
        from app.database.models import User, AWSAccount
        # Create User B with their own account
        user_b = User(cognito_sub="user-b-sub-2", email="b2@example.com", full_name="B")
        db.add(user_b)
        db.flush()
        acc_b = AWSAccount(
            user_id=user_b.id,
            account_name="User B Account",
            aws_account_id="999999999999",
            role_arn="arn:aws:iam::999999999999:role/Role",
            external_id="ext-b",
            connection_status="connected",
        )
        db.add(acc_b)
        db.commit()

        # User A lists accounts — should only see their own
        mock_user_a = {"user_id": test_user.cognito_sub, "email": test_user.email, "token": "t"}
        override_auth(mock_user_a)

        res = client.get("/accounts/")
        assert res.status_code == 200
        accounts = res.json()["accounts"]
        account_ids = [a["aws_account_id"] for a in accounts]
        assert "999999999999" not in account_ids   # User B's account not visible

        app.dependency_overrides.clear()

    def test_test_connection_own_account(self, client, test_user, test_account):
        mock_user = {"user_id": test_user.cognito_sub, "email": test_user.email, "token": "t"}
        override_auth(mock_user)

        with patch("app.services.account_service.validate_account_connection") as mock_v:
            mock_v.return_value = {"valid": True, "account_id": "123456789012"}

            res = client.post(f"/accounts/{test_account.id}/test")
            assert res.status_code == 200
            assert res.json()["valid"] == True

        app.dependency_overrides.clear()

    def test_disconnect_own_account(self, client, test_user, test_account):
        mock_user = {"user_id": test_user.cognito_sub, "email": test_user.email, "token": "t"}
        override_auth(mock_user)

        res = client.delete(f"/accounts/{test_account.id}")
        assert res.status_code == 200
        assert res.json()["success"] == True

        app.dependency_overrides.clear()


class TestSTSAssumeRole:
    def test_assume_role_success(self):
        with patch("boto3.client") as mock_boto:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId":     "ASIA_TEST",
                    "SecretAccessKey": "test-secret",
                    "SessionToken":    "test-session",
                    "Expiration":      "2099-01-01T00:00:00Z",
                }
            }
            mock_boto.return_value = mock_sts

            from app.services.aws_assume_role import assume_role
            creds = assume_role(
                "arn:aws:iam::123456789012:role/FinOpsRole",
                "finops-test-external-id",
            )
            assert creds["access_key_id"]     == "ASIA_TEST"
            assert creds["secret_access_key"] == "test-secret"
            assert "expiration" in creds

            # Verify ExternalId was passed
            call_kwargs = mock_sts.assume_role.call_args[1]
            assert call_kwargs["ExternalId"] == "finops-test-external-id"

    def test_assume_role_access_denied(self):
        with patch("boto3.client") as mock_boto:
            from botocore.exceptions import ClientError
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
                "assume_role"
            )
            mock_boto.return_value = mock_sts

            from app.services.aws_assume_role import assume_role
            with pytest.raises(ValueError) as exc:
                assume_role("arn:aws:iam::123:role/Bad", "wrong-external-id")
            assert "Access denied" in str(exc.value)

    def test_validate_connection(self):
        with patch("app.services.aws_assume_role.assume_role") as mock_assume:
            with patch("boto3.Session") as mock_session:
                mock_assume.return_value = {
                    "access_key_id":     "ASIA",
                    "secret_access_key": "secret",
                    "session_token":     "token",
                    "expiration":        "2099-01-01",
                }
                mock_sts = MagicMock()
                mock_sts.get_caller_identity.return_value = {
                    "Account": "123456789012",
                    "UserId":  "AIDTEST",
                    "Arn":     "arn:aws:sts::123456789012:assumed-role/FinOpsRole/session",
                }
                mock_session.return_value.client.return_value = mock_sts

                from app.services.aws_assume_role import validate_account_connection
                result = validate_account_connection(
                    "arn:aws:iam::123456789012:role/FinOpsRole",
                    "finops-ext-id",
                )
                assert result["valid"]      == True
                assert result["account_id"] == "123456789012"
