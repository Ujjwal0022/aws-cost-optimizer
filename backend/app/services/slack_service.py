"""
Slack Integration
- Send waste detection alerts to Slack webhook
- Weekly summary notifications
- Per-resource action buttons (view in AWS Console)
"""
import os
import httpx
from datetime import datetime, timezone
from app.services.aws_resources import fetch_all_recommendations
from app.services.aws_cost import fetch_cost_summary


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
AWS_CONSOLE_BASE  = "https://console.aws.amazon.com"

SEVERITY_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
TYPE_EMOJI     = {"EC2": "🖥️", "EBS": "💾", "EIP": "🌐", "RDS": "🗄️", "Snapshot": "📸"}


def _console_url(resource_type: str, resource_id: str, region: str) -> str:
    urls = {
        "EC2":      f"{AWS_CONSOLE_BASE}/ec2/v2/home?region={region}#Instances:instanceId={resource_id}",
        "EBS":      f"{AWS_CONSOLE_BASE}/ec2/v2/home?region={region}#Volumes:volumeId={resource_id}",
        "EIP":      f"{AWS_CONSOLE_BASE}/ec2/v2/home?region={region}#Addresses:",
        "RDS":      f"{AWS_CONSOLE_BASE}/rds/home?region={region}#database:id={resource_id}",
        "Snapshot": f"{AWS_CONSOLE_BASE}/ec2/v2/home?region={region}#Snapshots:snapshotId={resource_id}",
    }
    return urls.get(resource_type, AWS_CONSOLE_BASE)


def send_slack_message(payload: dict) -> dict:
    """Send a message to Slack via webhook."""
    if not SLACK_WEBHOOK_URL:
        return {"success": False, "error": "SLACK_WEBHOOK_URL not configured"}
    try:
        resp = httpx.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            return {"success": True, "message": "Sent to Slack"}
        return {"success": False, "error": f"Slack returned {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_waste_alert() -> dict:
    """Send idle/waste resource summary to Slack."""
    resources = fetch_all_recommendations()
    recs      = resources.recommendations

    if not recs:
        payload = {
            "text": "✅ *FinOps Scan Complete* — No waste detected! Your AWS account looks clean.",
        }
        return send_slack_message(payload)

    # Build blocks for top 5 recommendations
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚨 FinOps Waste Detection Alert", "emoji": True},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{len(recs)} waste item(s) detected* across your AWS account.\n"
                    f"💰 *Total potential savings: ${resources.total_estimated_savings:.2f}/month*"
                ),
            },
        },
        {"type": "divider"},
    ]

    for rec in recs[:5]:
        sev_emoji  = SEVERITY_EMOJI.get(rec.severity, "⚪")
        type_emoji = TYPE_EMOJI.get(rec.resource_type, "☁️")
        console_url = _console_url(rec.resource_type, rec.resource_id, rec.region)

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{sev_emoji} {type_emoji} *{rec.resource_type}* — `{rec.resource_id}`\n"
                    f"_{rec.issue.capitalize()}_ · *${rec.estimated_monthly_savings:.2f}/mo savings*\n"
                    f"{rec.recommendation[:120]}..."
                ),
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View in AWS"},
                "url": console_url,
                "action_id": f"view_{rec.resource_id}",
            },
        })

    if len(recs) > 5:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_...and {len(recs) - 5} more. Open FinOps dashboard for full report._"}],
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"_FinOps Cost Optimizer · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"}],
    })

    return send_slack_message({"blocks": blocks})


def send_weekly_summary() -> dict:
    """Send weekly cost summary to Slack."""
    cost    = fetch_cost_summary()
    resources = fetch_all_recommendations()

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📊 Weekly FinOps Cost Summary", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*MTD Spend*\n${cost.total_cost_mtd:.2f}"},
                {"type": "mrkdwn", "text": f"*Last Month*\n${cost.total_cost_last_month:.2f}"},
                {"type": "mrkdwn", "text": f"*Forecast*\n${cost.forecast_end_of_month:.2f}"},
                {"type": "mrkdwn", "text": f"*Potential Savings*\n${resources.total_estimated_savings:.2f}/mo"},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Top Services (MTD):*"},
        },
    ]

    for svc in cost.top_services[:5]:
        name = svc.service.replace("Amazon ", "").replace("AWS ", "")
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"• *{name}:* ${svc.amount:.4f}"}],
        })

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"_FinOps Cost Optimizer · Weekly Report · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}_"}],
    })

    return send_slack_message({"blocks": blocks})


def test_slack_connection() -> dict:
    """Send a test message to verify Slack webhook."""
    payload = {
        "text": "✅ *FinOps Cost Optimizer* — Slack integration is working! You'll receive waste alerts and weekly summaries here.",
    }
    return send_slack_message(payload)
