export interface CostByService { service: string; amount: number; currency: string; }
export interface DailyCost { date: string; amount: number; currency: string; }
export interface CostSummary {
  total_cost_mtd: number; total_cost_last_month: number;
  forecast_end_of_month: number; currency: string;
  top_services: CostByService[]; daily_trend: DailyCost[];
}
export interface ResourceRecommendation {
  resource_id: string; resource_type: string; region: string;
  issue: string; estimated_monthly_savings: number;
  recommendation: string; severity: "HIGH" | "MEDIUM" | "LOW";
}
export interface ResourceSummary {
  total_estimated_savings: number; currency: string;
  recommendations: ResourceRecommendation[];
}
export interface BudgetAlert {
  budget_name: string; budget_limit: number; actual_spend: number;
  forecasted_spend: number; alert_threshold_percent: number;
  status: "OK" | "WARNING" | "EXCEEDED";
}
