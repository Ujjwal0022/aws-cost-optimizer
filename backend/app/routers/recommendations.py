"""
Recommendations Router
GET  /recommendations              → all recommendations for selected account
GET  /recommendations/summary      → summary stats only
GET  /recommendations/category     → filter by category
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth.dependencies import get_current_user
from app.services.account_dependency import get_aws_for_account
from app.services.aws_client_factory import AWSClientFactory
from app.services.recommendation_service import (
    get_all_recommendations,
    get_ec2_recommendations,
    get_ebs_recommendations,
    get_eip_recommendations,
    get_rds_recommendations,
    get_lambda_recommendations,
    get_reserved_instance_recommendations,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/")
def list_recommendations(
    aws: AWSClientFactory = Depends(get_aws_for_account),
):
    """Get all recommendations for the selected AWS account."""
    try:
        return get_all_recommendations(aws)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def recommendations_summary(
    aws: AWSClientFactory = Depends(get_aws_for_account),
):
    """Get summary stats — count, total savings, breakdown by category."""
    try:
        data = get_all_recommendations(aws)
        summary = {
            "account_id":      data["account_id"],
            "account_name":    data["account_name"],
            "total_count":     data["total_count"],
            "monthly_savings": data["monthly_savings"],
            "annual_savings":  data["annual_savings"],
            "generated_at":    data["generated_at"],
            "by_category": {
                cat: {
                    "count":   len(recs),
                    "savings": round(sum(r["monthly_saving"] for r in recs), 2),
                }
                for cat, recs in data["by_category"].items()
            },
        }
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ec2")
def ec2_recommendations(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        return {"recommendations": get_ec2_recommendations(aws)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ebs")
def ebs_recommendations(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        return {"recommendations": get_ebs_recommendations(aws)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rds")
def rds_recommendations(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        return {"recommendations": get_rds_recommendations(aws)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reserved-instances")
def ri_recommendations(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        return {"recommendations": get_reserved_instance_recommendations(aws)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
