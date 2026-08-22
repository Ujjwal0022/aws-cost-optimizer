from fastapi import APIRouter, HTTPException
from app.services.aws_cost import fetch_cost_summary, fetch_budget_alerts
from app.models.schemas import CostSummaryResponse, BudgetAlert

router = APIRouter(prefix="/api/costs", tags=["costs"])

@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary():
    try: return fetch_cost_summary()
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/budgets", response_model=list[BudgetAlert])
async def get_budget_alerts():
    try: return fetch_budget_alerts()
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
