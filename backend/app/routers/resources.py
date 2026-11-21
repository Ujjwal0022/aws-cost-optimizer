"""
Account-Aware Resources Router
All endpoints require ?account_id=<id> and Bearer token.

GET /resources/ec2
GET /resources/ebs
GET /resources/eip
GET /resources/s3
GET /resources/rds
GET /resources/lambda
GET /resources/eks
GET /resources/waste
GET /resources/costs
GET /resources/costs/regions
"""

from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.services.account_dependency import get_aws_for_account
from app.services.aws_client_factory import AWSClientFactory
from app.services.ec2_service import (
    get_ec2_instances, get_unattached_ebs_volumes,
    get_unassociated_eips, get_security_groups_open_ssh,
)
from app.services.s3_service import get_s3_buckets
from app.services.rds_service import get_rds_instances
from app.services.lambda_eks_service import get_lambda_functions, get_eks_clusters
from app.services.cost_service import get_cost_summary, get_cost_by_region

router = APIRouter(prefix="/resources", tags=["Resources"])


# ── EC2 ───────────────────────────────────────────────────────────────────────
@router.get("/ec2")
def list_ec2(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        instances = get_ec2_instances(aws)
        idle      = [i for i in instances if i.get("is_idle")]
        return {
            "account_id": aws.account.aws_account_id,
            "region":     aws.account.default_region,
            "total":      len(instances),
            "idle":       len(idle),
            "instances":  instances,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── EBS ───────────────────────────────────────────────────────────────────────
@router.get("/ebs")
def list_ebs(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        volumes        = get_unattached_ebs_volumes(aws)
        total_savings  = sum(v["monthly_cost"] for v in volumes)
        return {
            "account_id":     aws.account.aws_account_id,
            "count":          len(volumes),
            "total_savings":  round(total_savings, 2),
            "volumes":        volumes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Elastic IPs ───────────────────────────────────────────────────────────────
@router.get("/eip")
def list_eip(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        eips          = get_unassociated_eips(aws)
        total_savings = sum(e["monthly_cost"] for e in eips)
        return {
            "account_id":    aws.account.aws_account_id,
            "count":         len(eips),
            "total_savings": round(total_savings, 2),
            "eips":          eips,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── S3 ────────────────────────────────────────────────────────────────────────
@router.get("/s3")
def list_s3(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        buckets = get_s3_buckets(aws)
        public  = [b for b in buckets if b.get("is_public")]
        return {
            "account_id":    aws.account.aws_account_id,
            "total":         len(buckets),
            "public_count":  len(public),
            "buckets":       buckets,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── RDS ───────────────────────────────────────────────────────────────────────
@router.get("/rds")
def list_rds(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        instances = get_rds_instances(aws)
        idle      = [i for i in instances if i.get("is_idle")]
        return {
            "account_id": aws.account.aws_account_id,
            "total":      len(instances),
            "idle":       len(idle),
            "instances":  instances,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Lambda ────────────────────────────────────────────────────────────────────
@router.get("/lambda")
def list_lambda(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        functions = get_lambda_functions(aws)
        idle      = [f for f in functions if f.get("is_idle")]
        return {
            "account_id": aws.account.aws_account_id,
            "total":      len(functions),
            "idle":       len(idle),
            "functions":  functions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── EKS ───────────────────────────────────────────────────────────────────────
@router.get("/eks")
def list_eks(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        clusters = get_eks_clusters(aws)
        return {
            "account_id": aws.account.aws_account_id,
            "total":      len(clusters),
            "clusters":   clusters,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Security Groups ───────────────────────────────────────────────────────────
@router.get("/security-groups")
def list_risky_sgs(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        risky = get_security_groups_open_ssh(aws)
        return {
            "account_id": aws.account.aws_account_id,
            "risky_count": len(risky),
            "groups":     risky,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Waste Summary ─────────────────────────────────────────────────────────────
@router.get("/waste")
def waste_summary(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        ebs  = get_unattached_ebs_volumes(aws)
        eips = get_unassociated_eips(aws)
        ec2  = [i for i in get_ec2_instances(aws) if i.get("is_idle")]
        rds  = [i for i in get_rds_instances(aws) if i.get("is_idle")]

        total_resources = len(ebs) + len(eips) + len(ec2) + len(rds)
        ebs_savings     = sum(v["monthly_cost"] for v in ebs)
        eip_savings     = sum(e["monthly_cost"] for e in eips)
        total_savings   = round(ebs_savings + eip_savings, 2)

        return {
            "account_id":        aws.account.aws_account_id,
            "account_name":      aws.account.account_name,
            "total_waste_items": total_resources,
            "monthly_savings":   total_savings,
            "annual_savings":    round(total_savings * 12, 2),
            "breakdown": {
                "unattached_ebs": {"count": len(ebs),  "savings": round(ebs_savings, 2), "items": ebs},
                "unassociated_eip": {"count": len(eips), "savings": round(eip_savings, 2), "items": eips},
                "idle_ec2":      {"count": len(ec2),  "savings": 0, "items": ec2},
                "idle_rds":      {"count": len(rds),  "savings": 0, "items": rds},
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Cost Summary ──────────────────────────────────────────────────────────────
@router.get("/costs")
def cost_summary(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        return get_cost_summary(aws)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/regions")
def cost_by_region(aws: AWSClientFactory = Depends(get_aws_for_account)):
    try:
        return {"regions": get_cost_by_region(aws)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
