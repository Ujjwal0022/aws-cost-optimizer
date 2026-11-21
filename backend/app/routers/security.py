"""
Security Router
GET /security/report   → full security report + score
GET /security/score    → score only
GET /security/iam      → IAM findings only
GET /security/s3       → S3 findings only
GET /security/sgs      → Security group findings only
"""

from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.services.account_dependency import get_aws_for_account
from app.services.aws_client_factory import AWSClientFactory
from app.services.security_service import (
    get_security_report, check_iam, check_s3,
    check_security_groups, compute_security_score,
)

router = APIRouter(prefix="/security", tags=["Security Center"])


@router.get("/report")
def security_report(aws: AWSClientFactory = Depends(get_aws_for_account)):
    """Full security posture report with score and all findings."""
    try:
        return get_security_report(aws)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score")
def security_score(aws: AWSClientFactory = Depends(get_aws_for_account)):
    """Security score only — faster than full report."""
    try:
        report = get_security_report(aws)
        return {
            "account_id":     report["account_id"],
            "security_score": report["security_score"],
            "grade":          report["grade"],
            "total_findings": report["total_findings"],
            "by_severity":    report["by_severity"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/iam")
def iam_findings(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        findings = check_iam(aws)
        return {"count": len(findings), "findings": findings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/s3")
def s3_findings(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        findings = check_s3(aws)
        return {"count": len(findings), "findings": findings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security-groups")
def sg_findings(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        findings = check_security_groups(aws)
        return {"count": len(findings), "findings": findings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
