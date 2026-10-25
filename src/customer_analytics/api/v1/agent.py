"""Guarded natural-language analytics agent endpoints."""

from fastapi import APIRouter, Depends

from customer_analytics.agent.answer_formatter import AgentAnalyticsResponse
from customer_analytics.api.dependencies import get_agent_service
from customer_analytics.api.v1.schemas import AgentAskRequest
from customer_analytics.application.agent_service import AgentService
from customer_analytics.observability.request_context import get_correlation_id

router = APIRouter(prefix="/agent", tags=["Analytics Agent"])


@router.post(
    "/ask",
    response_model=AgentAnalyticsResponse,
    summary="Ask Analytics Agent",
    description="Submit natural-language business questions and receive structured, evidence-backed answers.",
)
def ask_agent(
    req: AgentAskRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentAnalyticsResponse:
    cid = req.request_id or get_correlation_id()
    return service.process_question(question=req.question, request_id=cid)
