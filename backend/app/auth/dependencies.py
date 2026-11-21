"""Auth dependencies - Supabase JWT verification"""
import os
import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database.database import SessionLocal
from app.database.models import User

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

security = HTTPBearer()


def _ensure_user(uid: str, email: str, name: str) -> None:
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.cognito_sub == uid).first():
            db.add(User(cognito_sub=uid, email=email or f"{uid}@no-email.local", full_name=name))
            db.commit()
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        r = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {credentials.credentials}",
                "apikey": SUPABASE_ANON_KEY,
            },
            timeout=5,
        )
    except httpx.HTTPError as e:
        print(f"🔴 AUTH ERROR: Supabase unreachable - {e}")
        raise HTTPException(status_code=503, detail="Auth service unreachable")

    if r.status_code != 200:
        print(f"🔴 TOKEN ERROR: Supabase returned {r.status_code}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    u = r.json()
    meta = u.get("user_metadata") or {}
    name = meta.get("full_name") or meta.get("name", "")

    _ensure_user(u["id"], u.get("email"), name)

    return {
        "id": u["id"],
        "uid": u["id"],
        "user_id": u["id"],
        "sub": u["id"],
        "email": u.get("email"),
        "name": name,
        "full_name": name,
        "picture": meta.get("avatar_url", ""),
    }
