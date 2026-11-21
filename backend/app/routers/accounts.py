"""
Accounts Router — /accounts endpoints
GET    /accounts              → list user's connected AWS accounts
POST   /accounts              → connect new AWS account
GET    /accounts/{id}         → get single account
POST   /accounts/{id}/test    → test connection
DELETE /accounts/{id}         → disconnect account
GET    /accounts/{id}/setup   → get IAM setup instructions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.services.account_service import (
    list_accounts, connect_account, get_account,
    disconnect_account, test_account_connection,
    get_setup_instructions, generate_external_id,
)

router = APIRouter(prefix="/accounts", tags=["AWS Accounts"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class ConnectAccountRequest(BaseModel):
    account_name:   str   = Field(min_length=2, max_length=100, example="Production")
    aws_account_id: str   = Field(min_length=12, max_length=12, example="123456789012")
    role_arn:       str   = Field(example="arn:aws:iam::123456789012:role/FinOpsReadOnlyRole")
    default_region: str   = Field(default="us-east-1", example="us-east-1")


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/")
def list_aws_accounts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all AWS accounts connected by the current user."""
    return {
        "accounts": list_accounts(db, current_user["user_id"])
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def connect_aws_account(
    body: ConnectAccountRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Connect a new AWS account via cross-account IAM role.

    Flow:
    1. Generate unique ExternalId
    2. Validate STS AssumeRole with ExternalId
    3. Save account to database
    4. Return connection status + setup instructions if needed
    """
    try:
        result = connect_account(
            db=db,
            cognito_sub=current_user["user_id"],
            account_name=body.account_name,
            aws_account_id=body.aws_account_id,
            role_arn=body.role_arn,
            default_region=body.default_region,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/generate-external-id")
def get_external_id(current_user: dict = Depends(get_current_user)):
    """
    Generate a unique ExternalId before connecting an account.
    User needs this to configure the IAM role trust policy.
    """
    ext_id = generate_external_id(current_user["user_id"])
    return {
        "external_id": ext_id,
        "instructions": get_setup_instructions(ext_id),
    }


@router.get("/{account_id}")
def get_aws_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific AWS account (only owner can access)."""
    try:
        account = get_account(db, account_id, current_user["user_id"])
        return account.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{account_id}/test")
def test_connection(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test if the cross-account role can still be assumed."""
    try:
        return test_account_connection(db, account_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{account_id}")
def disconnect_aws_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect an AWS account (soft delete)."""
    try:
        return disconnect_account(db, account_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{account_id}/setup")
def get_iam_setup_instructions(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get IAM role setup instructions for this account's ExternalId."""
    try:
        account = get_account(db, account_id, current_user["user_id"])
        return get_setup_instructions(account.external_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
