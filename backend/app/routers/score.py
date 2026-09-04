from fastapi import APIRouter, HTTPException
from app.services.score_engine import calculate_optimization_score

router = APIRouter(prefix="/api/score", tags=["score"])


@router.get("/")
async def get_optimization_score():
    """Calculate and return the AWS Cost Optimization Score."""
    try:
        return calculate_optimization_score()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
