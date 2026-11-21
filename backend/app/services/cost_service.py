"""
Account-Aware Cost Explorer Service
"""

from datetime import datetime, timedelta
from app.services.aws_client_factory import AWSClientFactory


def get_cost_summary(aws: AWSClientFactory) -> dict:
    ce  = aws.cost_explorer()
    now = datetime.utcnow().date()

    # Current month
    curr_start = now.replace(day=1)
    curr_end   = now

    # Previous month
    prev_end   = curr_start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)

    def fetch_cost(start, end) -> float:
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": str(start), "End": str(end)},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        total = 0
        for r in resp.get("ResultsByTime", []):
            total += float(r["Total"]["UnblendedCost"]["Amount"])
        return round(total, 2)

    curr_cost = fetch_cost(curr_start, curr_end)
    prev_cost = fetch_cost(prev_start, prev_end)
    change    = round(((curr_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0, 1)

    # Daily costs for current month
    daily_resp = ce.get_cost_and_usage(
        TimePeriod={"Start": str(curr_start), "End": str(curr_end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    daily = [
        {
            "date": r["TimePeriod"]["Start"],
            "cost": round(float(r["Total"]["UnblendedCost"]["Amount"]), 2),
        }
        for r in daily_resp.get("ResultsByTime", [])
    ]

    # Top services
    svc_resp = ce.get_cost_and_usage(
        TimePeriod={"Start": str(curr_start), "End": str(curr_end)},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    services = []
    for r in svc_resp.get("ResultsByTime", []):
        for g in r.get("Groups", []):
            cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
            if cost > 0.01:
                services.append({
                    "service": g["Keys"][0],
                    "cost":    round(cost, 2),
                    "pct":     round(cost / curr_cost * 100, 1) if curr_cost > 0 else 0,
                })
    services.sort(key=lambda x: x["cost"], reverse=True)

    # Project month-end
    days_in_month  = (prev_end.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    days_elapsed   = (now - curr_start).days + 1
    daily_avg      = curr_cost / days_elapsed if days_elapsed > 0 else 0
    projected      = round(daily_avg * days_in_month.day, 2)

    return {
        "account_id":          aws.account.aws_account_id,
        "account_name":        aws.account.account_name,
        "current_month_cost":  curr_cost,
        "previous_month_cost": prev_cost,
        "month_over_month":    change,
        "projected_month_end": projected,
        "daily_avg":           round(daily_avg, 2),
        "daily_costs":         daily,
        "top_services":        services[:10],
        "period":              str(curr_start),
    }


def get_cost_by_region(aws: AWSClientFactory) -> list:
    ce    = aws.cost_explorer()
    now   = datetime.utcnow().date()
    start = now.replace(day=1)

    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(now)},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
    )
    regions = []
    for r in resp.get("ResultsByTime", []):
        for g in r.get("Groups", []):
            cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
            if cost > 0.01:
                regions.append({"region": g["Keys"][0], "cost": round(cost, 2)})
    return sorted(regions, key=lambda x: x["cost"], reverse=True)
