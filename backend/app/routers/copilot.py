"""
AI Copilot Router
POST /copilot/ask           → ask a question
GET  /copilot/suggestions   → get suggested questions
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import get_current_user
from app.services.account_dependency import get_aws_for_account
from app.services.aws_client_factory import AWSClientFactory
from app.services.copilot_service import ask_copilot, SUGGESTED_QUESTIONS

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


class ChatMessage(BaseModel):
    role:    str   # "user" or "assistant"
    content: str


class AskRequest(BaseModel):
    question:     str
    chat_history: Optional[list[ChatMessage]] = []


@router.post("/ask")
async def ask(
    body: AskRequest,
    aws: AWSClientFactory = Depends(get_aws_for_account),
    current_user: dict = Depends(get_current_user),
):
    """
    Ask the AI Copilot a question about your AWS costs.
    Uses real-time AWS data from the selected account as context.
    """
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        history = [{"role": m.role, "content": m.content} for m in (body.chat_history or [])]
        answer  = await ask_copilot(body.question, aws, history)
        return {
            "question": body.question,
            "answer":   answer,
            "account":  aws.account.account_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.get("/suggestions")
def get_suggestions():
    """Get suggested questions for the AI Copilot."""
    return {"suggestions": SUGGESTED_QUESTIONS}
