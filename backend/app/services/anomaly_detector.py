"""
AI-Powered Cost Anomaly Detection
- Uses Isolation Forest (scikit-learn) to detect unusual cost spikes
- Uses OpenAI/Gemini API to generate natural language explanation
- Falls back to rule-based explanation if AI unavailable
"""
import os
import json
import numpy as np
from datetime import datetime, timezone
from app.services.aws_cost import fetch_cost_summary
from app.config import settings


def _isolation_forest_detect(daily_amounts: list[float]) -> list[dict]:
    """Detect anomalies using Isolation Forest."""
    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np

        if len(daily_amounts) < 7:
            return []

        X = np.array(daily_amounts).reshape(-1, 1)
        model = IsolationForest(
            contamination=0.1,   # expect ~10% anomalies
            random_state=42,
            n_estimators=100,
        )
        predictions = model.fit_predict(X)
        scores      = model.score_samples(X)

        anomalies = []
        mean_cost = np.mean(daily_amounts)
        std_cost  = np.std(daily_amounts)

        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # anomaly detected
                amount    = daily_amounts[i]
                deviation = ((amount - mean_cost) / mean_cost * 100) if mean_cost > 0 else 0
                severity  = "HIGH" if abs(deviation) > 50 else "MEDIUM" if abs(deviation) > 25 else "LOW"
                anomalies.append({
                    "index":          i,
                    "amount":         round(amount, 4),
                    "mean_cost":      round(mean_cost, 4),
                    "deviation_pct":  round(deviation, 1),
                    "anomaly_score":  round(float(score), 4),
                    "severity":       severity,
                    "type":           "spike" if amount > mean_cost else "drop",
                })
        return anomalies

    except ImportError:
        # Fallback: simple z-score method
        return _zscore_detect(daily_amounts)


def _zscore_detect(daily_amounts: list[float]) -> list[dict]:
    """Fallback anomaly detection using z-score."""
    if len(daily_amounts) < 3:
        return []

    mean = sum(daily_amounts) / len(daily_amounts)
    variance = sum((x - mean) ** 2 for x in daily_amounts) / len(daily_amounts)
    std  = variance ** 0.5

    if std == 0:
        return []

    anomalies = []
    for i, amount in enumerate(daily_amounts):
        z_score = abs((amount - mean) / std)
        if z_score > 2.0:
            deviation = ((amount - mean) / mean * 100) if mean > 0 else 0
            severity  = "HIGH" if z_score > 3 else "MEDIUM"
            anomalies.append({
                "index":         i,
                "amount":        round(amount, 4),
                "mean_cost":     round(mean, 4),
                "deviation_pct": round(deviation, 1),
                "anomaly_score": round(float(-z_score), 4),
                "severity":      severity,
                "type":          "spike" if amount > mean else "drop",
            })
    return anomalies


def _get_ai_explanation(anomaly: dict, date: str, top_services: list) -> str:
    """Get AI-generated explanation for an anomaly."""
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if openai_key:
        try:
            import httpx
            services_str = ", ".join(
                f"{s['service']} (${s['amount']:.2f})"
                for s in top_services[:3]
            )
            prompt = (
                f"An AWS cost anomaly was detected on {date}. "
                f"Cost was ${anomaly['amount']:.2f}, which is {anomaly['deviation_pct']:+.1f}% "
                f"vs average of ${anomaly['mean_cost']:.2f}. "
                f"Top services: {services_str}. "
                f"In 2 sentences, explain what likely caused this and what action to take."
            )
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 120,
                },
                timeout=10,
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # Rule-based fallback
    return _rule_based_explanation(anomaly, date, top_services)


def _rule_based_explanation(anomaly: dict, date: str, top_services: list) -> str:
    """Generate explanation without AI."""
    dev = anomaly["deviation_pct"]
    typ = anomaly["type"]
    top = top_services[0]["service"].replace("Amazon ", "").replace("AWS ", "") if top_services else "EC2"

    if typ == "spike":
        if dev > 100:
            return (
                f"Significant cost spike detected on {date} (+{dev:.0f}%). "
                f"Likely caused by {top} scale-up event, new resource provisioning, or data transfer surge. "
                f"Review CloudTrail events for that date."
            )
        else:
            return (
                f"Cost increase of +{dev:.0f}% on {date}. "
                f"Possible causes: increased {top} usage or new services started. "
                f"Check AWS Cost Explorer for service breakdown."
            )
    else:
        return (
            f"Unusual cost drop of {dev:.0f}% on {date}. "
            f"This could indicate resources were stopped or deleted. "
            f"Verify all services are running as expected."
        )


def detect_anomalies() -> dict:
    """Main function — detect anomalies in daily cost trend."""
    cost_summary  = fetch_cost_summary()
    daily_trend   = cost_summary.daily_trend
    top_services  = [{"service": s.service, "amount": s.amount} for s in cost_summary.top_services]

    if not daily_trend:
        return {
            "anomalies_found": 0,
            "anomalies": [],
            "daily_trend": [],
            "mean_daily_cost": 0,
            "message": "Not enough data to detect anomalies.",
        }

    dates   = [d.date for d in daily_trend]
    amounts = [d.amount for d in daily_trend]
    mean    = sum(amounts) / len(amounts) if amounts else 0

    raw_anomalies = _isolation_forest_detect(amounts)

    enriched = []
    for a in raw_anomalies:
        idx  = a["index"]
        date = dates[idx] if idx < len(dates) else "unknown"
        explanation = _get_ai_explanation(a, date, top_services)
        enriched.append({
            **a,
            "date":        date,
            "explanation": explanation,
        })

    # Sort by severity
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    enriched.sort(key=lambda x: order.get(x["severity"], 3))

    return {
        "anomalies_found":  len(enriched),
        "anomalies":        enriched,
        "daily_trend":      [{"date": d.date, "amount": d.amount} for d in daily_trend],
        "mean_daily_cost":  round(mean, 4),
        "total_days_analyzed": len(daily_trend),
        "algorithm":        "Isolation Forest" if _try_sklearn() else "Z-Score",
        "analyzed_at":      datetime.now(timezone.utc).isoformat(),
    }


def _try_sklearn() -> bool:
    try:
        import sklearn
        return True
    except ImportError:
        return False
