import boto3
from datetime import date, timedelta
from app.config import settings
from app.models.schemas import CostSummaryResponse, CostByService, DailyCost, BudgetAlert


def _get_ce_client():
    return boto3.client(
        "ce",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )


def _get_budgets_client():
    return boto3.client(
        "budgets",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_DEFAULT_REGION,
    )


def fetch_cost_summary() -> CostSummaryResponse:
    ce = _get_ce_client()
    today = date.today()

    mtd_start = today.replace(day=1).isoformat()
    today_str = today.isoformat()

    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    # --- MTD total ---
    try:
        mtd_resp = ce.get_cost_and_usage(
            TimePeriod={"Start": mtd_start, "End": today_str},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        mtd_total = float(
            mtd_resp["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
        ) if mtd_resp["ResultsByTime"] else 0.0
    except Exception:
        mtd_total = 0.0

    # --- Last month total ---
    try:
        lm_resp = ce.get_cost_and_usage(
            TimePeriod={
                "Start": last_month_start.isoformat(),
                "End": first_of_this_month.isoformat(),
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        lm_total = float(
            lm_resp["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
        ) if lm_resp["ResultsByTime"] else 0.0
    except Exception:
        lm_total = 0.0

    # --- Forecast (may fail for new accounts) ---
    try:
        next_month_first = (today.replace(day=1).replace(month=today.month % 12 + 1)
                            if today.month < 12
                            else today.replace(year=today.year + 1, month=1, day=1))
        forecast_resp = ce.get_cost_forecast(
            TimePeriod={"Start": today_str, "End": next_month_first.isoformat()},
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY",
        )
        forecast_total = float(forecast_resp["Total"]["Amount"])
    except Exception:
        # New accounts don't have enough history — use MTD as estimate
        forecast_total = mtd_total

    # --- Top services MTD ---
    try:
        svc_resp = ce.get_cost_and_usage(
            TimePeriod={"Start": mtd_start, "End": today_str},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        services_raw = svc_resp["ResultsByTime"][0]["Groups"] if svc_resp["ResultsByTime"] else []
        top_services = sorted(
            [
                CostByService(
                    service=g["Keys"][0],
                    amount=round(float(g["Metrics"]["UnblendedCost"]["Amount"]), 4),
                )
                for g in services_raw
            ],
            key=lambda x: x.amount,
            reverse=True,
        )[:10]
    except Exception:
        top_services = []

    # --- Daily trend (last 30 days) ---
    try:
        daily_start = (today - timedelta(days=30)).isoformat()
        daily_resp = ce.get_cost_and_usage(
            TimePeriod={"Start": daily_start, "End": today_str},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
        )
        daily_trend = [
            DailyCost(
                date=r["TimePeriod"]["Start"],
                amount=round(float(r["Total"]["UnblendedCost"]["Amount"]), 4),
            )
            for r in daily_resp["ResultsByTime"]
        ]
    except Exception:
        daily_trend = []

    return CostSummaryResponse(
        total_cost_mtd=round(mtd_total, 4),
        total_cost_last_month=round(lm_total, 4),
        forecast_end_of_month=round(forecast_total, 4),
        top_services=top_services,
        daily_trend=daily_trend,
    )


def fetch_budget_alerts() -> list[BudgetAlert]:
    if not settings.AWS_ACCOUNT_ID:
        return []
    try:
        budgets_client = _get_budgets_client()
        resp = budgets_client.describe_budgets(AccountId=settings.AWS_ACCOUNT_ID)
        alerts = []
        for b in resp.get("Budgets", []):
            limit    = float(b["BudgetLimit"]["Amount"])
            actual   = float(b.get("CalculatedSpend", {}).get("ActualSpend",    {}).get("Amount", 0))
            forecast = float(b.get("CalculatedSpend", {}).get("ForecastedSpend",{}).get("Amount", 0))
            pct      = (actual / limit * 100) if limit else 0
            status   = "EXCEEDED" if pct >= 100 else "WARNING" if pct >= 80 else "OK"
            alerts.append(BudgetAlert(
                budget_name=b["BudgetName"],
                budget_limit=round(limit, 2),
                actual_spend=round(actual, 2),
                forecasted_spend=round(forecast, 2),
                alert_threshold_percent=round(pct, 2),
                status=status,
            ))
        return alerts
    except Exception:
        return []
