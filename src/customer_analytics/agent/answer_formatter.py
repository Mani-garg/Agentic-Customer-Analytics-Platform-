"""Agent response schema and formatting utilities."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentAnalyticsResponse(BaseModel):
    """Structured response contract for natural-language analytics inquiries."""

    request_id: str
    question: str
    answer: str
    intent: str
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    source_tools: List[str] = Field(default_factory=list)
    sql_statement: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    model_provider: str = "none"
    latency_ms: float = 0.0
    fallback_used: bool = False
