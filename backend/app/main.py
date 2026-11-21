from dotenv import load_dotenv
import os
load_dotenv()

"""
FinOps SaaS Platform — FastAPI Backend v6
All phases: Auth | Multi-Account | AWS APIs | Recommendations | Remediation | Security | AI Copilot
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth, accounts, resources, recommendations,
    remediation, audit, security, copilot,
    costs, advanced, score,
)
from app.database.database import create_tables

app = FastAPI(
    title="FinOps SaaS Platform",
    description="Multi-account AWS FinOps Automation & Governance Platform",
    version="6.0.0",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    create_tables()
    print("✅ Database ready — FinOps SaaS v6.0.0")


# ── All Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(resources.router)
app.include_router(recommendations.router)
app.include_router(remediation.router)
app.include_router(audit.router)
app.include_router(security.router)
app.include_router(copilot.router)
app.include_router(costs.router)       # Cost trends, by-service, anomalies
app.include_router(advanced.router)    # Forecast, anomaly detection
app.include_router(score.router)       # Optimization score

try:
    from app.routers import enterprise, alerts, reports
    app.include_router(enterprise.router)
    app.include_router(alerts.router)
    app.include_router(reports.router)
except ImportError:
    pass


@app.get("/")
async def root():
    return {
        "app":     "FinOps SaaS Platform",
        "version": "6.0.0",
        "phases":  ["auth", "multi-account", "aws-apis", "recommendations", "remediation", "security", "ai-copilot"],
        "docs":    "/docs",
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "6.0.0"}