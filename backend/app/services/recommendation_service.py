"""
FinOps Recommendation Engine
Generates actionable recommendations from real AWS data.
Each recommendation includes: resource, issue, action, savings, confidence, risk.
"""

from datetime import datetime, timedelta
from app.services.aws_client_factory import AWSClientFactory
from app.services.ec2_service import get_ec2_instances, get_unattached_ebs_volumes, get_unassociated_eips
from app.services.rds_service import get_rds_instances
from app.services.lambda_eks_service import get_lambda_functions


# ── EC2 Rightsizing Recommendations ──────────────────────────────────────────
EC2_RIGHTSIZING_MAP = {
    "t3.xlarge":  {"recommended": "t3.large",   "monthly_saving": 45.00},
    "t3.large":   {"recommended": "t3.medium",  "monthly_saving": 22.00},
    "t3.medium":  {"recommended": "t3.small",   "monthly_saving": 11.00},
    "m5.xlarge":  {"recommended": "m5.large",   "monthly_saving": 70.00},
    "m5.large":   {"recommended": "m5.medium",  "monthly_saving": 35.00},
    "m5.4xlarge": {"recommended": "m5.2xlarge", "monthly_saving": 140.00},
    "c5.xlarge":  {"recommended": "c5.large",   "monthly_saving": 60.00},
    "c5.large":   {"recommended": "c5.medium",  "monthly_saving": 30.00},
    "r5.xlarge":  {"recommended": "r5.large",   "monthly_saving": 90.00},
    "r5.large":   {"recommended": "r5.medium",  "monthly_saving": 45.00},
}

RDS_RIGHTSIZING_MAP = {
    "db.t3.large":   {"recommended": "db.t3.medium", "monthly_saving": 30.00},
    "db.t3.xlarge":  {"recommended": "db.t3.large",  "monthly_saving": 60.00},
    "db.m5.large":   {"recommended": "db.m5.medium", "monthly_saving": 50.00},
    "db.m5.xlarge":  {"recommended": "db.m5.large",  "monthly_saving": 100.00},
    "db.r5.large":   {"recommended": "db.r5.medium", "monthly_saving": 80.00},
    "db.r5.xlarge":  {"recommended": "db.r5.large",  "monthly_saving": 160.00},
}


def _rec(category, resource_type, resource_id, resource_name,
         issue, action, current_config, recommended_config,
         monthly_saving, confidence, risk, details=None):
    """Helper to build a recommendation dict."""
    return {
        "id":               f"{resource_type}-{resource_id}-{category}".lower().replace(" ", "-"),
        "category":         category,
        "resource_type":    resource_type,
        "resource_id":      resource_id,
        "resource_name":    resource_name,
        "issue":            issue,
        "action":           action,
        "current_config":   current_config,
        "recommended_config": recommended_config,
        "monthly_saving":   round(monthly_saving, 2),
        "annual_saving":    round(monthly_saving * 12, 2),
        "confidence":       confidence,       # 0-100
        "risk":             risk,             # LOW / MEDIUM / HIGH
        "details":          details or {},
        "created_at":       datetime.utcnow().isoformat(),
    }


# ── Generate EC2 Recommendations ─────────────────────────────────────────────
def get_ec2_recommendations(aws: AWSClientFactory) -> list:
    instances = get_ec2_instances(aws)
    recs      = []

    for inst in instances:
        if inst["state"] != "running":
            continue

        cpu         = inst.get("avg_cpu_7d")
        inst_type   = inst["instance_type"]
        instance_id = inst["instance_id"]
        name        = inst["name"]

        # ── Low CPU → rightsize ───────────────────────────────────────────────
        if cpu is not None and cpu < 5 and inst_type in EC2_RIGHTSIZING_MAP:
            sizing = EC2_RIGHTSIZING_MAP[inst_type]
            recs.append(_rec(
                category="RIGHTSIZING",
                resource_type="EC2",
                resource_id=instance_id,
                resource_name=name,
                issue=f"Average CPU utilization is only {cpu}% over 7 days",
                action=f"Downsize from {inst_type} to {sizing['recommended']}",
                current_config=inst_type,
                recommended_config=sizing["recommended"],
                monthly_saving=sizing["monthly_saving"],
                confidence=92,
                risk="LOW",
                details={"avg_cpu_7d": cpu, "region": inst.get("region")},
            ))

        # ── Very low CPU → stop instance ─────────────────────────────────────
        elif cpu is not None and cpu < 1:
            recs.append(_rec(
                category="IDLE_RESOURCE",
                resource_type="EC2",
                resource_id=instance_id,
                resource_name=name,
                issue=f"Instance appears idle — CPU utilization {cpu}% for 7 days",
                action="Stop or terminate this instance if not needed",
                current_config=f"Running — {inst_type}",
                recommended_config="Stopped",
                monthly_saving=25.00,
                confidence=85,
                risk="MEDIUM",
                details={"avg_cpu_7d": cpu, "region": inst.get("region")},
            ))

    return recs


# ── Generate EBS Recommendations ─────────────────────────────────────────────
def get_ebs_recommendations(aws: AWSClientFactory) -> list:
    volumes = get_unattached_ebs_volumes(aws)
    recs    = []

    for vol in volumes:
        recs.append(_rec(
            category="IDLE_RESOURCE",
            resource_type="EBS",
            resource_id=vol["volume_id"],
            resource_name=vol["volume_id"],
            issue=f"EBS volume unattached for {vol['age_days']} days",
            action="Delete unattached volume (create snapshot first if data needed)",
            current_config=f"{vol['size_gb']} GB {vol['volume_type']} — Unattached",
            recommended_config="Deleted (snapshot if needed)",
            monthly_saving=vol["monthly_cost"],
            confidence=95,
            risk="MEDIUM",
            details={
                "size_gb":   vol["size_gb"],
                "age_days":  vol["age_days"],
                "region":    vol["region"],
            },
        ))

    return recs


# ── Generate EIP Recommendations ─────────────────────────────────────────────
def get_eip_recommendations(aws: AWSClientFactory) -> list:
    eips = get_unassociated_eips(aws)
    recs = []

    for eip in eips:
        recs.append(_rec(
            category="IDLE_RESOURCE",
            resource_type="Elastic IP",
            resource_id=eip.get("allocation_id", eip["public_ip"]),
            resource_name=eip["public_ip"],
            issue="Elastic IP is not associated with any instance",
            action="Release unassociated Elastic IP",
            current_config=f"Unassociated — {eip['public_ip']}",
            recommended_config="Released",
            monthly_saving=eip["monthly_cost"],
            confidence=99,
            risk="LOW",
            details={"public_ip": eip["public_ip"], "region": eip["region"]},
        ))

    return recs


# ── Generate RDS Recommendations ─────────────────────────────────────────────
def get_rds_recommendations(aws: AWSClientFactory) -> list:
    instances = get_rds_instances(aws)
    recs      = []

    for db in instances:
        db_id    = db["db_id"]
        db_class = db["db_class"]
        conns    = db.get("avg_connections")

        # Idle RDS
        if conns is not None and conns < 1:
            recs.append(_rec(
                category="IDLE_RESOURCE",
                resource_type="RDS",
                resource_id=db_id,
                resource_name=db_id,
                issue=f"Database has 0 connections for 7 days",
                action="Stop or delete idle RDS instance",
                current_config=f"Running — {db_class} ({db['engine']})",
                recommended_config="Stopped",
                monthly_saving=50.00,
                confidence=90,
                risk="MEDIUM",
                details={"db_class": db_class, "avg_connections": conns},
            ))

        # Rightsize RDS
        elif conns is not None and conns < 5 and db_class in RDS_RIGHTSIZING_MAP:
            sizing = RDS_RIGHTSIZING_MAP[db_class]
            recs.append(_rec(
                category="RIGHTSIZING",
                resource_type="RDS",
                resource_id=db_id,
                resource_name=db_id,
                issue=f"Average connections only {conns:.1f} — instance may be oversized",
                action=f"Rightsize from {db_class} to {sizing['recommended']}",
                current_config=db_class,
                recommended_config=sizing["recommended"],
                monthly_saving=sizing["monthly_saving"],
                confidence=80,
                risk="MEDIUM",
                details={"avg_connections": conns, "engine": db["engine"]},
            ))

    return recs


# ── Generate Lambda Recommendations ──────────────────────────────────────────
def get_lambda_recommendations(aws: AWSClientFactory) -> list:
    functions = get_lambda_functions(aws)
    recs      = []

    for fn in functions:
        if fn.get("is_idle"):
            recs.append(_rec(
                category="IDLE_RESOURCE",
                resource_type="Lambda",
                resource_id=fn["function_name"],
                resource_name=fn["function_name"],
                issue="No invocations in the last 30 days",
                action="Delete unused Lambda function",
                current_config=f"{fn['runtime']} — {fn['memory_mb']}MB",
                recommended_config="Deleted",
                monthly_saving=0.50,
                confidence=80,
                risk="LOW",
                details={"runtime": fn["runtime"], "memory_mb": fn["memory_mb"]},
            ))

    return recs


# ── Reserved Instance Recommendation ─────────────────────────────────────────
def get_reserved_instance_recommendations(aws: AWSClientFactory) -> list:
    """Suggest Reserved Instances for consistently running EC2."""
    instances = get_ec2_instances(aws)
    recs      = []

    for inst in instances:
        if inst["state"] != "running":
            continue
        cpu       = inst.get("avg_cpu_7d")
        inst_type = inst["instance_type"]

        # Consistently used instances (CPU > 20%) → suggest RI
        if cpu is not None and cpu > 20:
            recs.append(_rec(
                category="RESERVED_INSTANCE",
                resource_type="EC2",
                resource_id=inst["instance_id"],
                resource_name=inst["name"],
                issue=f"Instance runs consistently at {cpu}% CPU — On-Demand pricing is expensive",
                action="Purchase 1-year Reserved Instance (saves ~40%)",
                current_config=f"On-Demand — {inst_type}",
                recommended_config=f"Reserved Instance (1yr) — {inst_type}",
                monthly_saving=30.00,
                confidence=75,
                risk="LOW",
                details={"avg_cpu_7d": cpu, "instance_type": inst_type},
            ))

    return recs[:3]  # Limit to top 3 RI suggestions


# ── Master function: all recommendations ─────────────────────────────────────
def get_all_recommendations(aws: AWSClientFactory) -> dict:
    ec2_recs  = get_ec2_recommendations(aws)
    ebs_recs  = get_ebs_recommendations(aws)
    eip_recs  = get_eip_recommendations(aws)
    rds_recs  = get_rds_recommendations(aws)
    lmb_recs  = get_lambda_recommendations(aws)
    ri_recs   = get_reserved_instance_recommendations(aws)

    all_recs  = ec2_recs + ebs_recs + eip_recs + rds_recs + lmb_recs + ri_recs

    # Sort by monthly saving descending
    all_recs.sort(key=lambda x: x["monthly_saving"], reverse=True)

    total_monthly = sum(r["monthly_saving"] for r in all_recs)
    total_annual  = total_monthly * 12

    by_category = {}
    for rec in all_recs:
        cat = rec["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(rec)

    return {
        "account_id":     aws.account.aws_account_id,
        "account_name":   aws.account.account_name,
        "total_count":    len(all_recs),
        "monthly_savings": round(total_monthly, 2),
        "annual_savings":  round(total_annual, 2),
        "by_category":    by_category,
        "recommendations": all_recs,
        "generated_at":   datetime.utcnow().isoformat(),
    }
