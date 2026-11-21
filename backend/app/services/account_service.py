"""
Account Service — Business logic for AWS account management
"""

import hashlib
import hmac
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import AWSAccount, User
from app.services.aws_assume_role import validate_account_connection

_EXT_ID_SECRET = os.getenv("EXTERNAL_ID_SECRET", "change-me-in-env").encode()


def generate_external_id(user_key: str) -> str:
    """Stable ExternalId per user: same user -> same ID, every time."""
    digest = hmac.new(_EXT_ID_SECRET, user_key.encode(), hashlib.sha256).digest()
    return f"finops-{uuid.UUID(bytes=digest[:16])}"


def get_user_from_cognito_sub(db: Session, cognito_sub: str) -> User:
    # cognito_sub column now stores the Supabase auth user id
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    if not user:
        raise ValueError("User not found")
    return user


def list_accounts(db: Session, cognito_sub: str) -> list:
    user = get_user_from_cognito_sub(db, cognito_sub)
    accounts = db.query(AWSAccount).filter(
        AWSAccount.user_id == user.id,
        AWSAccount.is_active == True,
    ).all()
    return [a.to_dict() for a in accounts]


def get_account(db: Session, account_id: str, cognito_sub: str) -> AWSAccount:
    """Get account and verify ownership — prevents IDOR attacks."""
    user = get_user_from_cognito_sub(db, cognito_sub)
    account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.user_id == user.id,   # ← CRITICAL: ownership check
        AWSAccount.is_active == True,
    ).first()
    if not account:
        raise ValueError("Account not found or access denied")
    return account


def connect_account(
    db: Session,
    cognito_sub: str,
    account_name: str,
    aws_account_id: str,
    role_arn: str,
    default_region: str = "us-east-1",
) -> dict:
    """
    Connect a new AWS account via cross-account IAM role.
    Uses the user's stable ExternalId, validates connection, saves to DB.
    """
    user = get_user_from_cognito_sub(db, cognito_sub)

    # Check for duplicate
    existing = db.query(AWSAccount).filter(
        AWSAccount.user_id == user.id,
        AWSAccount.aws_account_id == aws_account_id,
        AWSAccount.is_active == True,
    ).first()
    if existing:
        raise ValueError(f"AWS account {aws_account_id} is already connected.")

    # Same ID the user saw on screen (derived from cognito_sub)
    external_id = generate_external_id(cognito_sub)

    # Validate the connection before saving
    validation = validate_account_connection(role_arn, external_id, default_region)

    # Create account record
    account = AWSAccount(
        user_id=user.id,
        account_name=account_name,
        aws_account_id=aws_account_id,
        role_arn=role_arn,
        external_id=external_id,
        default_region=default_region,
        connection_status="connected" if validation["valid"] else "failed",
        last_synced_at=datetime.utcnow() if validation["valid"] else None,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    result = account.to_dict()
    if not validation["valid"]:
        result["warning"] = validation.get("error", "Connection validation failed")
        result["setup_instructions"] = get_setup_instructions(external_id)

    return result


def disconnect_account(db: Session, account_id: str, cognito_sub: str) -> dict:
    """Soft-delete an AWS account connection."""
    account = get_account(db, account_id, cognito_sub)
    account.is_active = False
    account.connection_status = "disconnected"
    db.commit()
    return {"success": True, "message": f"Account '{account.account_name}' disconnected."}


def test_account_connection(db: Session, account_id: str, cognito_sub: str) -> dict:
    """Re-test an existing account connection."""
    account = get_account(db, account_id, cognito_sub)
    validation = validate_account_connection(
        account.role_arn,
        account.external_id,
        account.default_region,
    )

    # Update status
    account.connection_status = "connected" if validation["valid"] else "failed"
    account.last_synced_at = datetime.utcnow() if validation["valid"] else account.last_synced_at
    db.commit()

    return {
        "account_id":    account_id,
        "account_name":  account.account_name,
        "valid":         validation["valid"],
        "details":       validation,
    }


def get_setup_instructions(external_id: str) -> dict:
    """
    Returns IAM setup instructions for the user to create
    FinOpsReadOnlyRole in their AWS account.
    """
    return {
        "step1": "Go to AWS IAM Console → Roles → Create Role",
        "step2": 'Select "Another AWS account" as trusted entity',
        "step3": "Enter the Platform Account ID (from your admin)",
        "step4": f'Add condition: "sts:ExternalId": "{external_id}"',
        "step5": "Attach policy: ReadOnlyAccess (or custom FinOpsPolicy)",
        "step6": 'Name the role: "FinOpsReadOnlyRole"',
        "step7": "Copy the Role ARN and paste it in the Connect Account form",
        "external_id": external_id,
        "trust_policy": {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::PLATFORM_ACCOUNT_ID:root"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"sts:ExternalId": external_id}
                }
            }]
        }
    }