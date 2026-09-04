"""
Cost Forecast Engine
- Linear regression on daily cost data
- Predicts next 30 days
- Confidence interval calculation
"""
from datetime import datetime, timezone, timedelta
from app.services.aws_cost import fetch_cost_summary


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """Simple linear regression — returns (slope, intercept)."""
    n    = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0
    sum_x  = sum(x)
    sum_y  = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_xx = sum(xi * xi for xi in x)
    denom  = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return 0.0, sum_y / n
    slope     = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _calc_rmse(actual: list[float], predicted: list[float]) -> float:
    if not actual:
        return 0.0
    mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)
    return mse ** 0.5


def generate_forecast() -> dict:
    """Generate 30-day cost forecast using linear regression."""
    cost_summary = fetch_cost_summary()
    daily_trend  = cost_summary.daily_trend

    if len(daily_trend) < 7:
        return {
            "forecast": [],
            "message": "Need at least 7 days of data for forecast.",
            "confidence": "low",
        }

    # Prepare training data
    amounts = [d.amount for d in daily_trend]
    x       = list(range(len(amounts)))
    slope, intercept = _linear_regression(x, amounts)

    # Calculate fit quality
    predicted_train = [slope * xi + intercept for xi in x]
    rmse = _calc_rmse(amounts, predicted_train)
    mean = sum(amounts) / len(amounts)
    r2   = 1 - (rmse ** 2 * len(amounts)) / (sum((a - mean) ** 2 for a in amounts) or 1)

    # Generate 30-day forecast
    last_date     = datetime.strptime(daily_trend[-1].date, "%Y-%m-%d")
    forecast_days = 30
    forecast      = []

    for i in range(1, forecast_days + 1):
        x_val          = len(amounts) + i - 1
        predicted_cost = max(0, slope * x_val + intercept)
        confidence_low = max(0, predicted_cost - 1.96 * rmse)
        confidence_hi  = predicted_cost + 1.96 * rmse
        forecast_date  = last_date + timedelta(days=i)

        forecast.append({
            "date":           forecast_date.strftime("%Y-%m-%d"),
            "predicted_cost": round(predicted_cost, 4),
            "confidence_low": round(confidence_low, 4),
            "confidence_high": round(confidence_hi, 4),
        })

    # Monthly summary
    next_month_total = sum(f["predicted_cost"] for f in forecast)
    current_mtd      = cost_summary.total_cost_mtd
    last_month       = cost_summary.total_cost_last_month

    # Trend direction
    if slope > 0.001:
        trend = "increasing"
        trend_emoji = "📈"
    elif slope < -0.001:
        trend = "decreasing"
        trend_emoji = "📉"
    else:
        trend = "stable"
        trend_emoji = "➡️"

    # Confidence level based on R²
    if r2 > 0.7:
        confidence = "high"
    elif r2 > 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "forecast":                forecast,
        "next_30_days_total":      round(next_month_total, 2),
        "current_mtd":             round(current_mtd, 2),
        "last_month_total":        round(last_month, 2),
        "daily_trend_actual":      [{"date": d.date, "amount": d.amount} for d in daily_trend],
        "trend_direction":         trend,
        "trend_emoji":             trend_emoji,
        "slope_per_day":           round(slope, 6),
        "model_accuracy":          {"r2": round(r2, 3), "rmse": round(rmse, 4)},
        "confidence":              confidence,
        "days_of_data_used":       len(amounts),
        "generated_at":            datetime.now(timezone.utc).isoformat(),
    }
