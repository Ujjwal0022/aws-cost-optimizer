"""
Audit Log Service
Query, filter, and retrieve audit logs from PostgreSQL.
"""

import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.database.models import AuditLog, AWSAccount, User


def get_audit_logs(
    db: Session,
    user_id: str,
    account_db_id: str = None,
    action: str = None,
    resource_type: str = None,
    status: str = None,
    days: int = 30,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    Fetch audit logs for the current user.
    Filters: account, action, resource_type, status, date range.
    """
    # Get user
    user = db.query(User).filter(User.cognito_sub == user_id).first()
    if not user:
        return {"logs": [], "total": 0}

    # Base query — only user's own logs
    query = db.query(AuditLog).filter(AuditLog.user_id == user.id)

    # Date filter
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(AuditLog.created_at >= since)

    # Optional filters
    if account_db_id:
        # Verify account belongs to user
        account = db.query(AWSAccount).filter(
            AWSAccount.id == account_db_id,
            AWSAccount.user_id == user.id,
        ).first()
        if account:
            query = query.filter(AuditLog.aws_account_id == account_db_id)

    if action:
        query = query.filter(AuditLog.action == action.upper())
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type.upper())
    if status:
        query = query.filter(AuditLog.status == status.lower())

    total = query.count()
    logs  = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    # Enrich with account name
    account_cache = {}
    result = []
    for log in logs:
        if log.aws_account_id and log.aws_account_id not in account_cache:
            acc = db.query(AWSAccount).filter(AWSAccount.id == log.aws_account_id).first()
            account_cache[log.aws_account_id] = acc.account_name if acc else "Unknown"

        entry = log.to_dict()
        entry["account_name"] = account_cache.get(log.aws_account_id, "—")
        try:
            entry["metadata"] = json.loads(log.metadata_json or "{}")
        except Exception:
            entry["metadata"] = {}
        result.append(entry)

    return {
        "logs":   result,
        "total":  total,
        "offset": offset,
        "limit":  limit,
    }


def get_audit_stats(db: Session, user_id: str) -> dict:
    """Summary stats for audit log page header."""
    user = db.query(User).filter(User.cognito_sub == user_id).first()
    if not user:
        return {}

    all_logs = db.query(AuditLog).filter(AuditLog.user_id == user.id).all()

    total_savings = sum(
        (log.estimated_saving or 0)
        for log in all_logs
        if log.status == "success"
    )

    by_status = {}
    by_action = {}
    for log in all_logs:
        by_status[log.status] = by_status.get(log.status, 0) + 1
        by_action[log.action] = by_action.get(log.action, 0) + 1

    return {
        "total_actions":    len(all_logs),
        "total_savings":    round(total_savings, 2),
        "by_status":        by_status,
        "top_actions":      sorted(by_action.items(), key=lambda x: x[1], reverse=True)[:5],
    }
