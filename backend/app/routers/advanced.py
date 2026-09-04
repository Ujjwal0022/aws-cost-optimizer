from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.score_engine import calculate_optimization_score
from app.services.anomaly_detector import detect_anomalies
from app.services.forecast_engine import generate_forecast
from app.services.slack_service import (
    send_waste_alert, send_weekly_summary, test_slack_connection
)

router = APIRouter(tags=["advanced"])


# ── Score ─────────────────────────────────────────────────────
@router.get("/api/score")
async def get_score():
    try:
        return calculate_optimization_score()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Anomaly Detection ─────────────────────────────────────────
@router.get("/api/anomalies")
async def get_anomalies():
    try:
        return detect_anomalies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Forecast ──────────────────────────────────────────────────
@router.get("/api/forecast")
async def get_forecast():
    try:
        return generate_forecast()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Slack ─────────────────────────────────────────────────────
@router.post("/api/slack/test")
async def slack_test():
    try:
        return test_slack_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/slack/waste-alert")
async def slack_waste_alert():
    try:
        return send_waste_alert()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/slack/weekly-summary")
async def slack_weekly():
    try:
        return send_weekly_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
