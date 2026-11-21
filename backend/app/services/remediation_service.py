"""
Remediation Service
Executes approved actions on AWS resources.
NEVER runs without explicit user approval.
Supports dry-run mode for safe previewing.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.aws_client_factory import AWSClientFactory
from app.database.models import AuditLog, AWSAccount, User


SUPPORTED_ACTIONS = {
    "STOP_EC2":      "Stop a running EC2 instance",
    "TERMINATE_EC2": "Terminate (permanently delete) an EC2 instance",
    "DELETE_EBS":    "Delete an unattached EBS volume",
    "RELEASE_EIP":   "Release an unassociated Elastic IP",
    "STOP_RDS":      "Stop a running RDS database instance",
    "DELETE_LAMBDA": "Delete an unused Lambda function",
}

DESTRUCTIVE_ACTIONS = {"TERMINATE_EC2", "DELETE_EBS", "RELEASE_EIP", "DELETE_LAMBDA"}


def _log_action(
    db: Session,
    user_id: str,
    account_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    description: str,
    estimated_saving: float,
    status: str,
    error_message: str = None,
    metadata: dict = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        aws_account_id=account_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        estimated_saving=estimated_saving,
        status=status,
        error_message=error_message,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ── Stop EC2 ──────────────────────────────────────────────────────────────────
def stop_ec2_instance(
    aws: AWSClientFactory,
    instance_id: str,
    db: Session,
    user_id: str,
    account_db_id: str,
    dry_run: bool = False,
    estimated_saving: float = 0.0,
    reason: str = "User-approved remediation",
) -> dict:
    if dry_run:
        log = _log_action(
            db, user_id, account_db_id,
            "STOP_EC2", "EC2", instance_id,
            f"[DRY RUN] Would stop EC2 instance {instance_id}. Reason: {reason}",
            estimated_saving, "dry_run",
        )
        return {
            "success": True, "dry_run": True,
            "message": f"[DRY RUN] Instance {instance_id} would be stopped.",
            "audit_log_id": log.id,
        }

    try:
        ec2 = aws.ec2()
        ec2.stop_instances(InstanceIds=[instance_id])
        log = _log_action(
            db, user_id, account_db_id,
            "STOP_EC2", "EC2", instance_id,
            f"Stopped EC2 instance {instance_id}. Reason: {reason}",
            estimated_saving, "success",
            metadata={"instance_id": instance_id, "reason": reason},
        )
        return {
            "success": True, "dry_run": False,
            "message": f"Instance {instance_id} is stopping.",
            "audit_log_id": log.id,
        }
    except Exception as e:
        log = _log_action(
            db, user_id, account_db_id,
            "STOP_EC2", "EC2", instance_id,
            f"Failed to stop EC2 {instance_id}", estimated_saving,
            "failed", str(e),
        )
        raise ValueError(f"Failed to stop instance: {str(e)}")


# ── Delete EBS Volume ─────────────────────────────────────────────────────────
def delete_ebs_volume(
    aws: AWSClientFactory,
    volume_id: str,
    db: Session,
    user_id: str,
    account_db_id: str,
    dry_run: bool = False,
    estimated_saving: float = 0.0,
    create_snapshot: bool = True,
    reason: str = "User-approved remediation",
) -> dict:
    if dry_run:
        log = _log_action(
            db, user_id, account_db_id,
            "DELETE_EBS", "EBS", volume_id,
            f"[DRY RUN] Would delete EBS volume {volume_id}",
            estimated_saving, "dry_run",
        )
        return {
            "success": True, "dry_run": True,
            "message": f"[DRY RUN] Volume {volume_id} would be deleted.",
            "snapshot_would_be_created": create_snapshot,
            "audit_log_id": log.id,
        }

    try:
        ec2      = aws.ec2()
        snapshot_id = None

        # Create safety snapshot before deletion
        if create_snapshot:
            snap = ec2.create_snapshot(
                VolumeId=volume_id,
                Description=f"FinOps safety snapshot before deletion — {datetime.utcnow().isoformat()}",
            )
            snapshot_id = snap["SnapshotId"]

        ec2.delete_volume(VolumeId=volume_id)

        log = _log_action(
            db, user_id, account_db_id,
            "DELETE_EBS", "EBS", volume_id,
            f"Deleted EBS volume {volume_id}. Snapshot: {snapshot_id or 'none'}. Reason: {reason}",
            estimated_saving, "success",
            metadata={"volume_id": volume_id, "snapshot_id": snapshot_id, "reason": reason},
        )
        return {
            "success": True, "dry_run": False,
            "message": f"Volume {volume_id} deleted.",
            "snapshot_id": snapshot_id,
            "audit_log_id": log.id,
        }
    except Exception as e:
        _log_action(
            db, user_id, account_db_id,
            "DELETE_EBS", "EBS", volume_id,
            f"Failed to delete EBS {volume_id}",
            estimated_saving, "failed", str(e),
        )
        raise ValueError(f"Failed to delete volume: {str(e)}")


# ── Release Elastic IP ────────────────────────────────────────────────────────
def release_elastic_ip(
    aws: AWSClientFactory,
    allocation_id: str,
    db: Session,
    user_id: str,
    account_db_id: str,
    dry_run: bool = False,
    estimated_saving: float = 3.60,
    reason: str = "User-approved remediation",
) -> dict:
    if dry_run:
        log = _log_action(
            db, user_id, account_db_id,
            "RELEASE_EIP", "Elastic IP", allocation_id,
            f"[DRY RUN] Would release EIP {allocation_id}",
            estimated_saving, "dry_run",
        )
        return {
            "success": True, "dry_run": True,
            "message": f"[DRY RUN] EIP {allocation_id} would be released.",
            "audit_log_id": log.id,
        }

    try:
        ec2 = aws.ec2()
        ec2.release_address(AllocationId=allocation_id)
        log = _log_action(
            db, user_id, account_db_id,
            "RELEASE_EIP", "Elastic IP", allocation_id,
            f"Released Elastic IP {allocation_id}. Reason: {reason}",
            estimated_saving, "success",
            metadata={"allocation_id": allocation_id, "reason": reason},
        )
        return {
            "success": True, "dry_run": False,
            "message": f"Elastic IP {allocation_id} released.",
            "audit_log_id": log.id,
        }
    except Exception as e:
        _log_action(
            db, user_id, account_db_id,
            "RELEASE_EIP", "Elastic IP", allocation_id,
            f"Failed to release EIP {allocation_id}",
            estimated_saving, "failed", str(e),
        )
        raise ValueError(f"Failed to release EIP: {str(e)}")


# ── Stop RDS ──────────────────────────────────────────────────────────────────
def stop_rds_instance(
    aws: AWSClientFactory,
    db_instance_id: str,
    db: Session,
    user_id: str,
    account_db_id: str,
    dry_run: bool = False,
    estimated_saving: float = 0.0,
    reason: str = "User-approved remediation",
) -> dict:
    if dry_run:
        log = _log_action(
            db, user_id, account_db_id,
            "STOP_RDS", "RDS", db_instance_id,
            f"[DRY RUN] Would stop RDS instance {db_instance_id}",
            estimated_saving, "dry_run",
        )
        return {
            "success": True, "dry_run": True,
            "message": f"[DRY RUN] RDS {db_instance_id} would be stopped.",
            "audit_log_id": log.id,
        }

    try:
        rds = aws.rds()
        rds.stop_db_instance(DBInstanceIdentifier=db_instance_id)
        log = _log_action(
            db, user_id, account_db_id,
            "STOP_RDS", "RDS", db_instance_id,
            f"Stopped RDS instance {db_instance_id}. Reason: {reason}",
            estimated_saving, "success",
            metadata={"db_instance_id": db_instance_id, "reason": reason},
        )
        return {
            "success": True, "dry_run": False,
            "message": f"RDS {db_instance_id} is stopping.",
            "audit_log_id": log.id,
        }
    except Exception as e:
        _log_action(
            db, user_id, account_db_id,
            "STOP_RDS", "RDS", db_instance_id,
            f"Failed to stop RDS {db_instance_id}",
            estimated_saving, "failed", str(e),
        )
        raise ValueError(f"Failed to stop RDS: {str(e)}")
