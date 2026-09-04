from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import costs, resources, reports, advanced
from app.config import settings

app = FastAPI(title="FinOps Cost Optimizer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(costs.router)
app.include_router(resources.router)
app.include_router(reports.router)
app.include_router(advanced.router)   # score + anomaly + forecast + slack


@app.get("/health")
async def health():
    return {"status": "ok", "service": "finops-api", "version": "2.0.0"}
