"""
Remediation Router
POST /remediation/stop-ec2
POST /remediation/delete-ebs
POST /remediation/release-eip
POST /remediation/stop-rds
GET  /remediation/supported-actions
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User, AWSAccount
from app.services.account_dependency import get_aws_for_account
from app.services.aws_client_factory import AWSClientFactory
from app.services.remediation_service import (
    stop_ec2_instance, delete_ebs_volume,
    release_elastic_ip, stop_rds_instance,
    SUPPORTED_ACTIONS, DESTRUCTIVE_ACTIONS,
)

router = APIRouter(prefix="/remediation", tags=["Remediation"])


# ── Helper: get user.id from cognito_sub ─────────────────────────────────────
def get_user_and_account(
    aws: AWSClientFactory,
    db: Session,
    current_user: dict,
) -> tuple[str, str]:
    user = db.query(User).filter(User.cognito_sub == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id, aws.account.id


# ── Schemas ───────────────────────────────────────────────────────────────────
class StopEC2Request(BaseModel):
    instance_id:      str
    dry_run:          bool  = True
    estimated_saving: float = 0.0
    reason:           str   = "User-approved via FinOps platform"


class DeleteEBSRequest(BaseModel):
    volume_id:        str
    dry_run:          bool  = True
    create_snapshot:  bool  = True
    estimated_saving: float = 0.0
    reason:           str   = "User-approved via FinOps platform"


class ReleaseEIPRequest(BaseModel):
    allocation_id:    str
    dry_run:          bool  = True
    estimated_saving: float = 3.60
    reason:           str   = "User-approved via FinOps platform"


class StopRDSRequest(BaseModel):
    db_instance_id:   str
    dry_run:          bool  = True
    estimated_saving: float = 0.0
    reason:           str   = "User-approved via FinOps platform"


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/supported-actions")
def list_supported_actions():
    return {
        "actions": [
            {
                "action":      action,
                "description": desc,
                "destructive": action in DESTRUCTIVE_ACTIONS,
            }
            for action, desc in SUPPORTED_ACTIONS.items()
        ]
    }


@router.post("/stop-ec2")
def stop_ec2(
    body: StopEC2Request,
    current_user: dict = Depends(get_current_user),
    aws: AWSClientFactory = Depends(get_aws_for_account),
    db: Session = Depends(get_db),
):
    """
    Stop a running EC2 instance.
    dry_run=true (default) → previews action without executing.
    dry_run=false → executes after explicit user approval.
    """
    user_id, account_db_id = get_user_and_account(aws, db, current_user)
    try:
        return stop_ec2_instance(
            aws=aws,
            instance_id=body.instance_id,
            db=db,
            user_id=user_id,
            account_db_id=account_db_id,
            dry_run=body.dry_run,
            estimated_saving=body.estimated_saving,
            reason=body.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete-ebs")
def delete_ebs(
    body: DeleteEBSRequest,
    current_user: dict = Depends(get_current_user),
    aws: AWSClientFactory = Depends(get_aws_for_account),
    db: Session = Depends(get_db),
):
    """
    Delete an unattached EBS volume.
    Creates a safety snapshot first (unless create_snapshot=false).
    """
    user_id, account_db_id = get_user_and_account(aws, db, current_user)
    try:
        return delete_ebs_volume(
            aws=aws,
            volume_id=body.volume_id,
            db=db,
            user_id=user_id,
            account_db_id=account_db_id,
            dry_run=body.dry_run,
            estimated_saving=body.estimated_saving,
            create_snapshot=body.create_snapshot,
            reason=body.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/release-eip")
def release_eip(
    body: ReleaseEIPRequest,
    current_user: dict = Depends(get_current_user),
    aws: AWSClientFactory = Depends(get_aws_for_account),
    db: Session = Depends(get_db),
):
    """Release an unassociated Elastic IP address."""
    user_id, account_db_id = get_user_and_account(aws, db, current_user)
    try:
        return release_elastic_ip(
            aws=aws,
            allocation_id=body.allocation_id,
            db=db,
            user_id=user_id,
            account_db_id=account_db_id,
            dry_run=body.dry_run,
            estimated_saving=body.estimated_saving,
            reason=body.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop-rds")
def stop_rds(
    body: StopRDSRequest,
    current_user: dict = Depends(get_current_user),
    aws: AWSClientFactory = Depends(get_aws_for_account),
    db: Session = Depends(get_db),
):
    """Stop an idle RDS database instance."""
    user_id, account_db_id = get_user_and_account(aws, db, current_user)
    try:
        return stop_rds_instance(
            aws=aws,
            db_instance_id=body.db_instance_id,
            db=db,
            user_id=user_id,
            account_db_id=account_db_id,
            dry_run=body.dry_run,
            estimated_saving=body.estimated_saving,
            reason=body.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
