"""Application service for natural-language analytics inquiries."""

from typing import Optional

from customer_analytics.agent.answer_formatter import AgentAnalyticsResponse
from customer_analytics.agent.factory import AnalyticsAgentService


class AgentService:
    """Orchestrates natural language question processing."""

    def __init__(self, agent: AnalyticsAgentService):
        self.agent = agent

    def process_question(
        self, question: str, request_id: Optional[str] = None
    ) -> AgentAnalyticsResponse:
        """Process incoming question through guarded analytics agent."""
        return self.agent.ask(question=question, request_id=request_id)
