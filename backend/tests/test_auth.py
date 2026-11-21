"""
Tests for authentication endpoints.
All Cognito calls are mocked — no real AWS needed.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestSignup:
    def test_signup_success(self, client):
        with patch("app.auth.cognito.get_cognito_client") as mock_cognito:
            mock_client = MagicMock()
            mock_client.sign_up.return_value = {
                "UserSub":       "new-user-sub-123",
                "UserConfirmed": False,
            }
            mock_cognito.return_value = mock_client

            res = client.post("/auth/signup", json={
                "email":     "newuser@example.com",
                "password":  "Test@1234!",
                "full_name": "New User",
            })
            assert res.status_code == 201
            data = res.json()
            assert "message" in data
            assert data["confirmed"] == False

    def test_signup_duplicate_email(self, client):
        with patch("app.auth.cognito.get_cognito_client") as mock_cognito:
            from botocore.exceptions import ClientError
            mock_client = MagicMock()
            mock_client.sign_up.side_effect = ClientError(
                {"Error": {"Code": "UsernameExistsException", "Message": "User already exists"}},
                "sign_up"
            )
            mock_cognito.return_value = mock_client

            res = client.post("/auth/signup", json={
                "email":     "existing@example.com",
                "password":  "Test@1234!",
                "full_name": "Existing User",
            })
            assert res.status_code == 400
            assert "already exists" in res.json()["detail"]

    def test_signup_missing_fields(self, client):
        res = client.post("/auth/signup", json={"email": "test@test.com"})
        assert res.status_code == 422   # Validation error

    def test_signup_invalid_email(self, client):
        res = client.post("/auth/signup", json={
            "email":     "not-an-email",
            "password":  "Test@1234!",
            "full_name": "Test User",
        })
        assert res.status_code == 422


class TestLogin:
    def test_login_success(self, client, test_user, db):
        with patch("app.auth.cognito.get_cognito_client") as mock_cognito:
            import jwt
            # Create a fake ID token
            id_token = jwt.encode(
                {"sub": test_user.cognito_sub, "email": test_user.email, "name": test_user.full_name},
                "secret", algorithm="HS256"
            )
            mock_client = MagicMock()
            mock_client.initiate_auth.return_value = {
                "AuthenticationResult": {
                    "AccessToken":  "mock-access-token",
                    "IdToken":      id_token,
                    "RefreshToken": "mock-refresh-token",
                    "ExpiresIn":    3600,
                }
            }
            mock_cognito.return_value = mock_client

            res = client.post("/auth/login", json={
                "email":    test_user.email,
                "password": "Test@1234!",
            })
            assert res.status_code == 200
            data = res.json()
            assert "access_token" in data
            assert "refresh_token" in data

    def test_login_wrong_password(self, client):
        with patch("app.auth.cognito.get_cognito_client") as mock_cognito:
            from botocore.exceptions import ClientError
            mock_client = MagicMock()
            mock_client.initiate_auth.side_effect = ClientError(
                {"Error": {"Code": "NotAuthorizedException", "Message": "Incorrect username or password."}},
                "initiate_auth"
            )
            mock_cognito.return_value = mock_client

            res = client.post("/auth/login", json={
                "email":    "test@example.com",
                "password": "wrongpassword",
            })
            assert res.status_code == 401
            assert "Invalid email or password" in res.json()["detail"]

    def test_login_unconfirmed_user(self, client):
        with patch("app.auth.cognito.get_cognito_client") as mock_cognito:
            from botocore.exceptions import ClientError
            mock_client = MagicMock()
            mock_client.initiate_auth.side_effect = ClientError(
                {"Error": {"Code": "UserNotConfirmedException", "Message": "User not confirmed."}},
                "initiate_auth"
            )
            mock_cognito.return_value = mock_client

            res = client.post("/auth/login", json={
                "email":    "unconfirmed@example.com",
                "password": "Test@1234!",
            })
            assert res.status_code == 401
            assert "verify your email" in res.json()["detail"]


class TestProtectedRoute:
    def test_me_requires_auth(self, client):
        res = client.get("/auth/me")
        assert res.status_code == 403   # No auth header

    def test_me_invalid_token(self, client):
        res = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert res.status_code == 401
