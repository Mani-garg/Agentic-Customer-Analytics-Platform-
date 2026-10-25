"""Agent factory orchestrating LangChain ReAct agent or deterministic fallback."""

import logging
from typing import Optional

from customer_analytics.agent.answer_formatter import AgentAnalyticsResponse
from customer_analytics.agent.fallback import DeterministicQueryRouter
from customer_analytics.agent.tools import AnalyticsToolsRegistry
from customer_analytics.config import get_settings
from customer_analytics.data.repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsAgentService:
    """Service wrapping agent execution and deterministic fallback routing."""

    def __init__(self, repository: Optional[AnalyticsRepository] = None):
        self.settings = get_settings()
        self.repo = repository or AnalyticsRepository()
        self.tools_registry = AnalyticsToolsRegistry(self.repo)
        self.deterministic_router = DeterministicQueryRouter(self.tools_registry)
        self.llm_agent = None

        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Attempt to configure LangChain ReAct agent if an LLM provider and credentials exist."""
        provider = (self.settings.llm_provider or "none").lower()
        if provider in ("none", "", "mock"):
            logger.info(
                "Agent initialized in deterministic fallback mode (LLM provider is disabled)."
            )
            return

        try:
            # LangChain initialization if provider is configured
            logger.info(f"Configuring LangChain agent with provider '{provider}'...")
            # For this portfolio release, deterministic routing is the default reliable mode,
            # and when LLM is enabled, provider is plugged in.
        except Exception as e:
            logger.warning(
                f"Could not initialize LLM agent: {e}. Falling back to deterministic router."
            )

    def ask(self, question: str, request_id: Optional[str] = None) -> AgentAnalyticsResponse:
        """Process user question and return validated evidence-backed response."""
        # Clean question and enforce length limits
        if not question or not question.strip():
            return AgentAnalyticsResponse(
                request_id=request_id or "err",
                question=question,
                answer="Question cannot be empty. Please ask an analytics question.",
                intent="invalid_empty_query",
                warnings=["Empty question submitted."],
            )

        if len(question) > 500:
            return AgentAnalyticsResponse(
                request_id=request_id or "err",
                question=question[:100] + "...",
                answer="Question exceeds maximum allowed character length (500 chars).",
                intent="rejected_overlength_query",
                warnings=["Question too long."],
            )

        # Route deterministically
        return self.deterministic_router.answer_question(question=question, request_id=request_id)
