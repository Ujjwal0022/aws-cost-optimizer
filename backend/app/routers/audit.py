"""
Audit Router
GET /audit              → list audit logs with filters
GET /audit/stats        → summary stats
GET /audit/{log_id}     → single log detail
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.services.audit_service import get_audit_logs, get_audit_stats

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/")
def list_audit_logs(
    account_id:    str = Query(None),
    action:        str = Query(None),
    resource_type: str = Query(None),
    status:        str = Query(None),
    days:          int = Query(30, ge=1, le=365),
    limit:         int = Query(50, ge=1, le=200),
    offset:        int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List audit logs for the current user with optional filters."""
    return get_audit_logs(
        db=db,
        user_id=current_user["user_id"],
        account_db_id=account_id,
        action=action,
        resource_type=resource_type,
        status=status,
        days=days,
        limit=limit,
        offset=offset,
    )


@router.get("/stats")
def audit_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Summary stats — total actions, savings, breakdown by status."""
    return get_audit_stats(db, current_user["user_id"])
