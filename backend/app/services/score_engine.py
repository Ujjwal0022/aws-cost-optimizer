"""
AWS Cost Optimization Score Engine
Calculates a 0-100 score based on multiple dimensions:
  - EC2 Utilization
  - Storage Waste
  - Unused IPs
  - Cost Trend (MoM change)
  - Budget Health
"""
import boto3
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.services.aws_resources import fetch_all_recommendations
from app.services.aws_cost import fetch_cost_summary


# ── Weight of each dimension (must sum to 100) ────────────────
WEIGHTS = {
    "ec2_utilization":  30,
    "storage_waste":    20,
    "unused_ips":       15,
    "cost_trend":       20,
    "budget_health":    15,
}


def _ec2(region=None):
    return boto3.client(
        "ec2",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION,
    )


def _cw(region=None):
    return boto3.client(
        "cloudwatch",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION,
    )


def _score_label(score: float) -> dict:
    if score >= 90:
        return {"label": "Excellent", "color": "#276749", "bg": "#F0FFF4", "emoji": "🟢"}
    elif score >= 75:
        return {"label": "Good",      "color": "#2B6CB0", "bg": "#EBF8FF", "emoji": "🔵"}
    elif score >= 60:
        return {"label": "Fair",      "color": "#975A16", "bg": "#FFFBEB", "emoji": "🟡"}
    elif score >= 40:
        return {"label": "Poor",      "color": "#C05621", "bg": "#FFFAF0", "emoji": "🟠"}
    else:
        return {"label": "Critical",  "color": "#C53030", "bg": "#FFF5F5", "emoji": "🔴"}


# ── Dimension 1: EC2 Utilization ──────────────────────────────
def _calc_ec2_utilization() -> dict:
    """
    Score: 100 if all EC2s have CPU > 20%
           Decreases for each idle instance
    """
    try:
        ec2 = _ec2()
        cw  = _cw()
        instances = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        all_insts = [
            i
            for r in instances["Reservations"]
            for i in r["Instances"]
        ]
        if not all_insts:
            return {"score": 100, "value": "No instances", "detail": "No running EC2 instances found.", "status": "ok"}

        idle_count = 0
        total = len(all_insts)
        end   = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        for inst in all_insts:
            iid  = inst["InstanceId"]
            resp = cw.get_metric_statistics(
                Namespace="AWS/EC2", MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": iid}],
                StartTime=start, EndTime=end, Period=86400, Statistics=["Average"],
            )
            pts = resp["Datapoints"]
            avg = sum(d["Average"] for d in pts) / len(pts) if pts else 0.0
            if avg < 10.0:
                idle_count += 1

        idle_pct = (idle_count / total) * 100
        score    = max(0, 100 - (idle_pct * 1.5))
        return {
            "score":  round(score),
            "value":  f"{total - idle_count}/{total} utilized",
            "detail": f"{idle_count} idle instance(s) with CPU < 10% over 7 days.",
            "status": "ok" if idle_count == 0 else "warning" if idle_count <= 2 else "critical",
        }
    except Exception as e:
        return {"score": 70, "value": "N/A", "detail": str(e), "status": "unknown"}


# ── Dimension 2: Storage Waste ────────────────────────────────
def _calc_storage_waste() -> dict:
    """
    Score: 100 if no unattached EBS / old snapshots
    """
    try:
        ec2 = _ec2()
        vols  = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
        snaps = ec2.describe_snapshots(OwnerIds=[settings.AWS_ACCOUNT_ID or "self"])
        cutoff    = datetime.now(timezone.utc) - timedelta(days=30)
        old_snaps = [s for s in snaps["Snapshots"] if s["StartTime"] < cutoff]
        waste_count = len(vols["Volumes"]) + len(old_snaps)
        score = max(0, 100 - (waste_count * 15))
        return {
            "score":  round(score),
            "value":  f"{len(vols['Volumes'])} unattached EBS, {len(old_snaps)} old snapshots",
            "detail": f"{waste_count} storage waste item(s) detected.",
            "status": "ok" if waste_count == 0 else "warning",
        }
    except Exception as e:
        return {"score": 70, "value": "N/A", "detail": str(e), "status": "unknown"}


# ── Dimension 3: Unused IPs ───────────────────────────────────
def _calc_unused_ips() -> dict:
    try:
        ec2   = _ec2()
        addrs = ec2.describe_addresses()
        unused = [a for a in addrs["Addresses"] if "AssociationId" not in a]
        score  = max(0, 100 - (len(unused) * 20))
        return {
            "score":  round(score),
            "value":  f"{len(unused)} unused EIP(s)",
            "detail": f"{len(unused)} Elastic IP(s) not associated with any instance.",
            "status": "ok" if len(unused) == 0 else "warning",
        }
    except Exception as e:
        return {"score": 80, "value": "N/A", "detail": str(e), "status": "unknown"}


# ── Dimension 4: Cost Trend ───────────────────────────────────
def _calc_cost_trend(cost_summary) -> dict:
    """
    Score: 100 if cost decreased or flat MoM
           Decreases as cost grows month-over-month
    """
    try:
        mtd  = cost_summary.total_cost_mtd
        last = cost_summary.total_cost_last_month
        if last == 0:
            return {"score": 80, "value": "First month", "detail": "No previous month data.", "status": "ok"}

        # Annualize MTD to full month for fair comparison
        day_of_month = datetime.now().day
        days_in_month = 30
        projected = (mtd / day_of_month) * days_in_month
        change_pct = ((projected - last) / last) * 100

        if change_pct <= 0:
            score = 100
        elif change_pct <= 10:
            score = 85
        elif change_pct <= 25:
            score = 65
        elif change_pct <= 50:
            score = 40
        else:
            score = 20

        trend = f"+{change_pct:.1f}%" if change_pct > 0 else f"{change_pct:.1f}%"
        return {
            "score":  round(score),
            "value":  trend + " vs last month",
            "detail": f"Projected spend ${projected:.2f} vs last month ${last:.2f}.",
            "status": "ok" if change_pct <= 10 else "warning" if change_pct <= 30 else "critical",
        }
    except Exception as e:
        return {"score": 70, "value": "N/A", "detail": str(e), "status": "unknown"}


# ── Dimension 5: Budget Health ────────────────────────────────
def _calc_budget_health() -> dict:
    try:
        if not settings.AWS_ACCOUNT_ID:
            return {"score": 80, "value": "No budgets", "detail": "AWS Account ID not set.", "status": "unknown"}

        budgets_client = boto3.client(
            "budgets",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        )
        resp     = budgets_client.describe_budgets(AccountId=settings.AWS_ACCOUNT_ID)
        budgets  = resp.get("Budgets", [])
        if not budgets:
            return {"score": 80, "value": "No budgets", "detail": "No AWS Budgets configured.", "status": "unknown"}

        exceeded = 0
        warning  = 0
        for b in budgets:
            limit  = float(b["BudgetLimit"]["Amount"])
            actual = float(b.get("CalculatedSpend", {}).get("ActualSpend", {}).get("Amount", 0))
            pct    = (actual / limit * 100) if limit else 0
            if pct >= 100:
                exceeded += 1
            elif pct >= 80:
                warning += 1

        score = 100 - (exceeded * 30) - (warning * 15)
        score = max(0, score)
        return {
            "score":  round(score),
            "value":  f"{exceeded} exceeded, {warning} warning",
            "detail": f"Out of {len(budgets)} budget(s): {exceeded} exceeded, {warning} near limit.",
            "status": "critical" if exceeded > 0 else "warning" if warning > 0 else "ok",
        }
    except Exception as e:
        return {"score": 75, "value": "N/A", "detail": str(e), "status": "unknown"}


# ── Main Score Calculator ─────────────────────────────────────
def calculate_optimization_score() -> dict:
    cost_summary = fetch_cost_summary()
    resources    = fetch_all_recommendations()

    dimensions = {
        "ec2_utilization": _calc_ec2_utilization(),
        "storage_waste":   _calc_storage_waste(),
        "unused_ips":      _calc_unused_ips(),
        "cost_trend":      _calc_cost_trend(cost_summary),
        "budget_health":   _calc_budget_health(),
    }

    # Weighted total score
    total_score = sum(
        dimensions[dim]["score"] * (WEIGHTS[dim] / 100)
        for dim in WEIGHTS
    )
    total_score = round(total_score)
    label_info  = _score_label(total_score)

    # Top recommendations from waste detector
    top_recs = [
        {
            "text": r.recommendation[:100] + "..." if len(r.recommendation) > 100 else r.recommendation,
            "savings": r.estimated_monthly_savings,
            "severity": r.severity,
            "type": r.resource_type,
        }
        for r in resources.recommendations[:3]
    ]

    return {
        "overall_score":          total_score,
        "label":                  label_info["label"],
        "color":                  label_info["color"],
        "bg":                     label_info["bg"],
        "emoji":                  label_info["emoji"],
        "total_potential_savings": resources.total_estimated_savings,
        "dimensions": {
            "ec2_utilization": {
                "name":   "EC2 Utilization",
                "weight": WEIGHTS["ec2_utilization"],
                "icon":   "🖥️",
                **dimensions["ec2_utilization"],
            },
            "storage_waste": {
                "name":   "Storage Efficiency",
                "weight": WEIGHTS["storage_waste"],
                "icon":   "💾",
                **dimensions["storage_waste"],
            },
            "unused_ips": {
                "name":   "IP Management",
                "weight": WEIGHTS["unused_ips"],
                "icon":   "🌐",
                **dimensions["unused_ips"],
            },
            "cost_trend": {
                "name":   "Cost Trend",
                "weight": WEIGHTS["cost_trend"],
                "icon":   "📈",
                **dimensions["cost_trend"],
            },
            "budget_health": {
                "name":   "Budget Health",
                "weight": WEIGHTS["budget_health"],
                "icon":   "💰",
                **dimensions["budget_health"],
            },
        },
        "top_recommendations": top_recs,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }
