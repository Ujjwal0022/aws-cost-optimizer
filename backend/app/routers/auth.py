"""
Auth Router — /auth endpoints
POST /auth/signup
POST /auth/verify
POST /auth/login
POST /auth/logout
POST /auth/refresh
POST /auth/forgot-password
POST /auth/reset-password
GET  /auth/me
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.auth.cognito import (
    signup_user, confirm_signup, login_user,
    logout_user, refresh_tokens, forgot_password,
    confirm_forgot_password,
)
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User, NotificationPreference

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email:     EmailStr
    password:  str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class VerifyRequest(BaseModel):
    email: EmailStr
    code:  str


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str
    email:         EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email:        EmailStr
    code:         str
    new_password: str = Field(min_length=8)


# ── Helper: get or create user in DB ─────────────────────────────────────────
def get_or_create_user(db: Session, cognito_sub: str, email: str, name: str) -> User:
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    if not user:
        user = User(
            cognito_sub=cognito_sub,
            email=email,
            full_name=name,
        )
        db.add(user)
        db.flush()

        # Create default notification preferences
        prefs = NotificationPreference(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(user)
    return user


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest):
    """Register a new user via Cognito."""
    try:
        result = signup_user(body.email, body.password, body.full_name)
        return {
            "message":   result["message"],
            "confirmed": result["confirmed"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
def verify_email(body: VerifyRequest):
    """Verify email with confirmation code sent by Cognito."""
    try:
        return confirm_signup(body.email, body.code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive JWT tokens."""
    try:
        tokens = login_user(body.email, body.password)

        # Decode sub from id_token without full verification (already verified by Cognito)
        import jwt as pyjwt
        id_payload = pyjwt.decode(tokens["id_token"], options={"verify_signature": False})
        cognito_sub = id_payload.get("sub", "")
        name        = id_payload.get("name", "")

        # Ensure user exists in our DB
        get_or_create_user(db, cognito_sub, body.email, name)

        return tokens
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Invalidate the current session in Cognito."""
    try:
        return logout_user(current_user["token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
def refresh(body: RefreshRequest):
    """Get new access token using refresh token."""
    try:
        return refresh_tokens(body.refresh_token, body.email)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/forgot-password")
def forgot_password_route(body: ForgotPasswordRequest):
    """Send password reset code to email."""
    try:
        return forgot_password(body.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    """Reset password with code from email."""
    try:
        return confirm_forgot_password(body.email, body.code, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user profile."""
    user = db.query(User).filter(User.cognito_sub == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        **user.to_dict(),
        "cognito_sub": current_user["user_id"],
    }
