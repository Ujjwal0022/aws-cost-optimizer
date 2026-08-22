from fastapi import APIRouter, HTTPException
from app.services.aws_resources import fetch_all_recommendations
from app.models.schemas import ResourceSummaryResponse

router = APIRouter(prefix="/api/resources", tags=["resources"])

@router.get("/recommendations", response_model=ResourceSummaryResponse)
async def get_recommendations():
    try: return fetch_all_recommendations()
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
