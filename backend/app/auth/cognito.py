"""
app/auth/cognito.py
Wrapper around AWS Cognito for all auth operations.
Uses USER_PASSWORD_AUTH flow (must be enabled on App Client — already done ✅)
"""

import boto3
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError
from app.config import settings  # adjust import if your config path differs


# ── Boto3 client ──────────────────────────────────────────────────────────────
def _get_client():
    return boto3.client("cognito-idp", region_name=settings.AWS_REGION)


# ── Secret hash (needed if App Client has a client secret) ────────────────────
def _secret_hash(username: str) -> str | None:
    """
    Returns HMAC-SHA256 secret hash if COGNITO_CLIENT_SECRET is set.
    If your App Client has NO secret, this returns None and we skip it.
    """
    secret = getattr(settings, "COGNITO_CLIENT_SECRET", None)
    if not secret:
        return None
    msg = username + settings.COGNITO_CLIENT_ID
    digest = hmac.new(
        secret.encode("utf-8"),
        msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode()


def _auth_params(username: str, password: str) -> dict:
    """Build AuthParameters dict, including SECRET_HASH only if needed."""
    params: dict = {
        "USERNAME": username,
        "PASSWORD": password,
    }
    sh = _secret_hash(username)
    if sh:
        params["SECRET_HASH"] = sh
    return params


def _refresh_params(username: str, refresh_token: str) -> dict:
    params: dict = {"REFRESH_TOKEN": refresh_token}
    sh = _secret_hash(username)
    if sh:
        params["SECRET_HASH"] = sh
    return params


# ── signup_user ───────────────────────────────────────────────────────────────
def signup_user(email: str, password: str, full_name: str) -> dict:
    client = _get_client()
    kwargs: dict = {
        "ClientId": settings.COGNITO_CLIENT_ID,
        "Username": email,
        "Password": password,
        "UserAttributes": [
            {"Name": "email", "Value": email},
            {"Name": "name",  "Value": full_name},
        ],
    }
    sh = _secret_hash(email)
    if sh:
        kwargs["SecretHash"] = sh

    try:
        resp = client.sign_up(**kwargs)
        confirmed = resp.get("UserConfirmed", False)
        return {
            "message":   "Signup successful. Check your email for verification code."
                         if not confirmed else "Signup successful.",
            "confirmed": confirmed,
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code == "UsernameExistsException":
            raise ValueError("An account with this email already exists.")
        raise ValueError(f"Signup failed: {msg}")


# ── confirm_signup ────────────────────────────────────────────────────────────
def confirm_signup(email: str, code: str) -> dict:
    client = _get_client()
    kwargs: dict = {
        "ClientId":        settings.COGNITO_CLIENT_ID,
        "Username":        email,
        "ConfirmationCode": code,
    }
    sh = _secret_hash(email)
    if sh:
        kwargs["SecretHash"] = sh

    try:
        client.confirm_sign_up(**kwargs)
        return {"message": "Email verified successfully. You can now log in."}
    except ClientError as e:
        code_name = e.response["Error"]["Code"]
        msg       = e.response["Error"]["Message"]
        if code_name == "CodeMismatchException":
            raise ValueError("Invalid verification code.")
        if code_name == "ExpiredCodeException":
            raise ValueError("Verification code has expired. Please request a new one.")
        raise ValueError(f"Verification failed: {msg}")


# ── login_user ────────────────────────────────────────────────────────────────
def login_user(email: str, password: str) -> dict:
    """
    Authenticate with USER_PASSWORD_AUTH flow.
    ✅ This is the flow enabled in your Cognito App Client.
    """
    client = _get_client()
    try:
        resp = client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",          # ← THE FIX
            AuthParameters=_auth_params(email, password),
            ClientId=settings.COGNITO_CLIENT_ID,
        )
        auth = resp.get("AuthenticationResult", {})
        if not auth:
            raise ValueError("Authentication failed: no tokens returned.")

        return {
            "access_token":  auth["AccessToken"],
            "id_token":      auth["IdToken"],
            "refresh_token": auth["RefreshToken"],
            "token_type":    "Bearer",
            "expires_in":    auth.get("ExpiresIn", 3600),
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]

        error_map = {
            "NotAuthorizedException":       "Invalid email or password.",
            "UserNotFoundException":        "No account found with this email.",
            "UserNotConfirmedException":    "Please verify your email before logging in.",
            "PasswordResetRequiredException": "Password reset required. Please reset your password.",
            "TooManyRequestsException":     "Too many attempts. Please try again later.",
        }
        raise ValueError(error_map.get(code, f"Login failed: {msg}"))


# ── logout_user ───────────────────────────────────────────────────────────────
def logout_user(access_token: str) -> dict:
    """Global sign-out — invalidates all tokens for this session."""
    client = _get_client()
    try:
        client.global_sign_out(AccessToken=access_token)
        return {"message": "Logged out successfully."}
    except ClientError as e:
        msg = e.response["Error"]["Message"]
        raise ValueError(f"Logout failed: {msg}")


# ── refresh_tokens ────────────────────────────────────────────────────────────
def refresh_tokens(refresh_token: str, email: str) -> dict:
    """Get new access + id tokens using the refresh token."""
    client = _get_client()
    try:
        resp = client.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters=_refresh_params(email, refresh_token),
            ClientId=settings.COGNITO_CLIENT_ID,
        )
        auth = resp.get("AuthenticationResult", {})
        return {
            "access_token": auth["AccessToken"],
            "id_token":     auth["IdToken"],
            "token_type":   "Bearer",
            "expires_in":   auth.get("ExpiresIn", 3600),
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code in ("NotAuthorizedException", "TokenExpiredException"):
            raise ValueError("Refresh token expired or invalid. Please log in again.")
        raise ValueError(f"Token refresh failed: {msg}")


# ── forgot_password ───────────────────────────────────────────────────────────
def forgot_password(email: str) -> dict:
    """Trigger Cognito to send password reset code to email."""
    client = _get_client()
    kwargs: dict = {
        "ClientId": settings.COGNITO_CLIENT_ID,
        "Username": email,
    }
    sh = _secret_hash(email)
    if sh:
        kwargs["SecretHash"] = sh

    try:
        client.forgot_password(**kwargs)
        return {"message": "Password reset code sent to your email."}
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code == "UserNotFoundException":
            # Don't reveal whether email exists — security best practice
            return {"message": "If this email exists, a reset code has been sent."}
        raise ValueError(f"Password reset failed: {msg}")


# ── confirm_forgot_password ───────────────────────────────────────────────────
def confirm_forgot_password(email: str, code: str, new_password: str) -> dict:
    """Complete the password reset flow with the code from email."""
    client = _get_client()
    kwargs: dict = {
        "ClientId":         settings.COGNITO_CLIENT_ID,
        "Username":         email,
        "ConfirmationCode": code,
        "Password":         new_password,
    }
    sh = _secret_hash(email)
    if sh:
        kwargs["SecretHash"] = sh

    try:
        client.confirm_forgot_password(**kwargs)
        return {"message": "Password reset successful. You can now log in."}
    except ClientError as e:
        code_name = e.response["Error"]["Code"]
        msg       = e.response["Error"]["Message"]
        if code_name == "CodeMismatchException":
            raise ValueError("Invalid reset code.")
        if code_name == "ExpiredCodeException":
            raise ValueError("Reset code has expired. Please request a new one.")
        if code_name == "InvalidPasswordException":
            raise ValueError(f"Password does not meet requirements: {msg}")
        raise ValueError(f"Password reset failed: {msg}")