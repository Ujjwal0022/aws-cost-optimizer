from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from app.services.aws_cost import fetch_cost_summary
from app.services.aws_resources import fetch_all_recommendations
from app.services.report_generator import generate_csv, generate_excel, generate_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/csv")
async def download_csv():
    try:
        content = generate_csv(fetch_all_recommendations())
        return StreamingResponse(io.BytesIO(content), media_type="text/csv",
            headers={"Content-Disposition":"attachment; filename=finops_report.csv"})
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/excel")
async def download_excel():
    try:
        content = generate_excel(fetch_all_recommendations(), fetch_cost_summary())
        return StreamingResponse(io.BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition":"attachment; filename=finops_report.xlsx"})
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf")
async def download_pdf():
    try:
        content = generate_pdf(fetch_all_recommendations(), fetch_cost_summary())
        return StreamingResponse(io.BytesIO(content), media_type="application/pdf",
            headers={"Content-Disposition":"attachment; filename=finops_report.pdf"})
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
