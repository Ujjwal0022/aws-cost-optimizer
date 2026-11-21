"""
Account-Aware Dependency Injection
Provides AWSClientFactory to any route that needs it.

Usage in routes:
    @router.get("/ec2")
    def list_ec2(aws: AWSClientFactory = Depends(get_aws_for_account)):
        ec2 = aws.ec2()
        ...
"""

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import AWSAccount, User
from app.services.aws_client_factory import AWSClientFactory


def get_aws_for_account(
    account_id: str = Query(..., description="Connected AWS account ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AWSClientFactory:
    """
    FastAPI dependency — validates account ownership and returns AWSClientFactory.

    Security:
    - Verifies the account belongs to the current user (prevents IDOR)
    - Creates temporary AWS session via STS AssumeRole
    - Credentials expire in 1 hour
    """
    # Get user from DB
    user = db.query(User).filter(User.cognito_sub == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get account — MUST belong to current user
    account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.user_id == user.id,       # ← ownership check
        AWSAccount.is_active == True,
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="AWS account not found or access denied",
        )

    if account.connection_status == "disconnected":
        raise HTTPException(
            status_code=400,
            detail="This AWS account has been disconnected",
        )

    try:
        return AWSClientFactory(account)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to AWS account: {str(e)}",
        )
