from pydantic import BaseModel

class CostByService(BaseModel):
    service: str
    amount: float
    currency: str = "USD"

class DailyCost(BaseModel):
    date: str
    amount: float
    currency: str = "USD"

class CostSummaryResponse(BaseModel):
    total_cost_mtd: float
    total_cost_last_month: float
    forecast_end_of_month: float
    currency: str = "USD"
    top_services: list[CostByService]
    daily_trend: list[DailyCost]

class ResourceRecommendation(BaseModel):
    resource_id: str
    resource_type: str
    region: str
    issue: str
    estimated_monthly_savings: float
    recommendation: str
    severity: str

class ResourceSummaryResponse(BaseModel):
    total_estimated_savings: float
    currency: str = "USD"
    recommendations: list[ResourceRecommendation]

class BudgetAlert(BaseModel):
    budget_name: str
    budget_limit: float
    actual_spend: float
    forecasted_spend: float
    alert_threshold_percent: float
    status: str
