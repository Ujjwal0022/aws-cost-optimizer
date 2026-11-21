from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth.dependencies import get_current_user
from app.services.aws_cost import fetch_cost_summary, fetch_budget_alerts
try:
    from app.services.anomaly_detector import detect_anomalies
except ImportError:
    def detect_anomalies(): return {"anomalies": [], "error": "anomaly_detector unavailable"}
from app.services.forecast_engine import generate_forecast
from app.models.schemas import CostSummaryResponse, BudgetAlert
import boto3
from datetime import date, timedelta
from app.config import settings

router = APIRouter(prefix="/api/costs", tags=["costs"])

def _ce(account_id: str, role_arn: str = None):
    if role_arn:
        sts = boto3.client(
            "sts",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        creds = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="finops-session",
        )["Credentials"]
        return boto3.client(
            "ce", region_name="us-east-1",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )
    return boto3.client(
        "ce", region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

@router.get("/summary")
async def get_cost_summary(
    account_id: str = Query(None),
    period: str = Query("30d"),
    user=Depends(get_current_user),
):
    try:
        return fetch_cost_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/budgets")
async def get_budget_alerts(user=Depends(get_current_user)):
    try:
        return fetch_budget_alerts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trend")
async def get_trend(
    account_id: str = Query(...),
    period: str = Query("30d"),
    user=Depends(get_current_user),
):
    days = {"7d": 7, "30d": 30, "90d": 90, "mtd": None}.get(period, 30)
    today = date.today()
    start = (today - timedelta(days=days)).isoformat() if days else today.replace(day=1).isoformat()
    end = today.isoformat()
    try:
        ce = _ce(account_id)
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
        )
        return {"trends": [
            {"date": r["TimePeriod"]["Start"],
             "cost": round(float(r["Total"]["UnblendedCost"]["Amount"]), 4)}
            for r in resp["ResultsByTime"]
        ]}
    except Exception as e:
        return {"trends": [], "error": str(e)}

@router.get("/by-service")
async def get_by_service(
    account_id: str = Query(...),
    period: str = Query("30d"),
    user=Depends(get_current_user),
):
    days = {"7d": 7, "30d": 30, "90d": 90, "mtd": None}.get(period, 30)
    today = date.today()
    start = (today.replace(day=1) if not days else today - timedelta(days=days)).isoformat()
    end = today.isoformat()
    try:
        ce = _ce(account_id)
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        groups = resp["ResultsByTime"][0]["Groups"] if resp["ResultsByTime"] else []
        return {"services": sorted(
            [{"service": g["Keys"][0],
              "cost": round(float(g["Metrics"]["UnblendedCost"]["Amount"]), 4)}
             for g in groups],
            key=lambda x: x["cost"], reverse=True
        )}
    except Exception as e:
        return {"services": [], "error": str(e)}

@router.get("/anomalies")
async def get_anomalies(
    account_id: str = Query(None),
    user=Depends(get_current_user),
):
    try:
        result = detect_anomalies()
        if isinstance(result, dict):
            return result
        return {"anomalies": result if isinstance(result, list) else []}
    except Exception as e:
        return {"anomalies": [], "error": str(e)}

@router.get("/forecast")
async def get_forecast_costs(
    account_id: str = Query(None),
    period: str = Query("30d"),
    user=Depends(get_current_user),
):
    try:
        result = generate_forecast()
        if isinstance(result, dict):
            return result
        return {"forecast": result, "trends": []}
    except Exception as e:
        return {"forecast": None, "trends": [], "error": str(e)}


@router.get("/by-region")
async def get_by_region(
    account_id: str = Query(...),
    period: str = Query("30d"),
    user=Depends(get_current_user),
):
    days = {"7d": 7, "30d": 30, "90d": 90, "mtd": None}.get(period, 30)
    today = date.today()
    start = (today.replace(day=1) if not days else today - timedelta(days=days)).isoformat()
    end = today.isoformat()
    try:
        ce = _ce(account_id)
        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
        )
        groups = resp["ResultsByTime"][0]["Groups"] if resp["ResultsByTime"] else []
        return {"regions": sorted(
            [{"region": g["Keys"][0],
              "cost": round(float(g["Metrics"]["UnblendedCost"]["Amount"]), 4)}
             for g in groups],
            key=lambda x: x["cost"], reverse=True
        )}
    except Exception as e:
        return {"regions": [], "error": str(e)}
