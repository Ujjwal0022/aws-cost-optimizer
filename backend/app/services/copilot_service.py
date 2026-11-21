import os
import httpx
import json
from datetime import datetime
from app.services.aws_client_factory import AWSClientFactory
from app.services.aws_cost import fetch_cost_summary as get_cost_summary
from app.services.ec2_service import get_ec2_instances, get_unattached_ebs_volumes
from app.services.recommendation_service import get_all_recommendations

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.1-8b-instant"

def build_context(aws: AWSClientFactory) -> str:
    parts = [
        f"AWS Account: {aws.account.account_name} ({aws.account.aws_account_id})",
        f"Region: {aws.account.default_region}",
        f"Analyzed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    # Cost data
    try:
        costs = fetch_cost_summary()
        parts += [
            "=== COST DATA ===",
            f"Current month cost: ${costs.get('current_month_cost', 'N/A')}",
            f"Previous month cost: ${costs.get('previous_month_cost', 'N/A')}",
            f"Month-over-month change: {costs.get('month_over_month', 'N/A')}%",
            f"Projected month-end: ${costs.get('projected_month_end', 'N/A')}",
            f"Daily average: ${costs.get('daily_avg', 'N/A')}",
            "Top services by cost:",
        ]
        for svc in costs.get("top_services", [])[:6]:
            parts.append(f"  - {svc['service']}: ${svc['cost']} ({svc.get('pct', '')}%)")
        parts.append("")
    except Exception as e:
        parts.append(f"Cost data: unavailable ({str(e)[:50]})")

    # EC2 instances
    try:
        instances = get_ec2_instances(aws)
        running = [i for i in instances if i["state"] == "running"]
        idle    = [i for i in running if i.get("is_idle")]
        parts += [
            "=== EC2 INSTANCES ===",
            f"Total instances: {len(instances)}",
            f"Running: {len(running)}",
            f"Idle (CPU < 5%): {len(idle)}",
        ]
        for inst in idle[:3]:
            parts.append(
                f"  - {inst.get('name', inst['instance_id'])} ({inst['instance_id']}): "
                f"{inst['instance_type']}, CPU={inst.get('avg_cpu_7d', 'N/A')}%"
            )
        parts.append("")
    except Exception as e:
        parts.append(f"EC2 data: unavailable ({str(e)[:50]})")

    # Waste
    try:
        volumes = get_unattached_ebs_volumes(aws)
        savings = sum(v["monthly_cost"] for v in volumes)
        parts += [
            "=== WASTE DETECTED ===",
            f"Unattached EBS volumes: {len(volumes)}",
            f"EBS waste cost: ${savings:.2f}/month",
            "",
        ]
    except Exception as e:
        parts.append(f"Waste data: unavailable ({str(e)[:50]})")

    # Recommendations
    try:
        recs = get_all_recommendations(aws)
        parts += [
            "=== RECOMMENDATIONS ===",
            f"Total recommendations: {recs['total_count']}",
            f"Potential monthly savings: ${recs['monthly_savings']}",
            f"Potential annual savings: ${recs['annual_savings']}",
        ]
        for rec in recs.get("recommendations", [])[:4]:
            parts.append(
                f"  - {rec['resource_type']} {rec['resource_id']}: "
                f"{rec['issue']} → Save ${rec['monthly_saving']}/mo"
            )
        parts.append("")
    except Exception as e:
        parts.append(f"Recommendations: unavailable ({str(e)[:50]})")

    return "\n".join(parts)


async def ask_copilot(question: str, aws: AWSClientFactory, chat_history: list = None) -> str:
    if not GROQ_API_KEY:
        return "AI Copilot is not configured. Please set the GROQ_API_KEY environment variable."

    aws_context = build_context(aws)

    system_prompt = f"""You are an expert AWS FinOps Copilot assistant embedded in a cloud cost optimization platform.
You have access to REAL-TIME data from the user's AWS account. Always base your answers on this actual data.
Never make up numbers or hallucinate AWS resource details.

CURRENT AWS ACCOUNT DATA:
{aws_context}

INSTRUCTIONS:
- Answer questions using the real data above
- Be specific with numbers, resource IDs, and service names from the data
- Give actionable, concise recommendations
- If data is unavailable for something, say so clearly
- Keep answers under 200 words unless a detailed breakdown is requested
- Use $ signs for costs and % for percentages
- Format responses clearly with bullet points when listing items"""

    messages = []
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "max_tokens": 1024,
                "temperature": 0.3,
                "system": system_prompt,
                "messages": messages,
            },
        )
        data = response.json()

    if response.status_code != 200:
        raise ValueError(f"Groq API error: {data.get('error', {}).get('message', 'Unknown error')}")

    return data["choices"][0]["message"]["content"]


SUGGESTED_QUESTIONS = [
    "Why did my AWS bill increase this month?",
    "Which service costs the most?",
    "How can I save $100 this month?",
    "Which EC2 instances are wasting money?",
    "What caused the biggest cost spike?",
    "What should I optimize first?",
    "How much am I projected to spend this month?",
    "Which resources should I delete to save money?",
]
