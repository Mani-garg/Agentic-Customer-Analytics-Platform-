"""Deterministic rule-based query router and fallback for natural-language inquiries."""

import json
import logging
import time
import uuid
from typing import Optional

from customer_analytics.agent.answer_formatter import AgentAnalyticsResponse
from customer_analytics.agent.tools import AnalyticsToolsRegistry

logger = logging.getLogger(__name__)


class DeterministicQueryRouter:
    """Answers common analytical questions deterministically without requiring an LLM."""

    def __init__(self, tools_registry: AnalyticsToolsRegistry):
        self.tools = tools_registry

    def answer_question(
        self, question: str, request_id: Optional[str] = None
    ) -> AgentAnalyticsResponse:
        """Route user query to appropriate analytical tools and return structured evidence response."""
        start_time = time.perf_counter()
        req_id = request_id or str(uuid.uuid4())
        q_lower = question.lower().strip()

        # 1. Segment Revenue inquiry
        if any(term in q_lower for term in ["segment", "segments"]) and any(
            term in q_lower for term in ["revenue", "spend", "sales", "contribute"]
        ):
            raw = self.tools.get_rfm_segment_summary()
            summaries = json.loads(raw)
            top_seg = summaries[0] if summaries else {}
            ans = (
                f"Based on RFM segmentation, the segment contributing the highest total revenue is "
                f"'{top_seg.get('segment')}' with ${top_seg.get('total_revenue', 0):,.2f} in sales "
                f"({top_seg.get('customer_percentage', 0)}% of customers, ARPU: ${top_seg.get('average_revenue_per_customer', 0):,.2f})."
            )
            return AgentAnalyticsResponse(
                request_id=req_id,
                question=question,
                answer=ans,
                intent="segment_revenue_analysis",
                summary_metrics={
                    "top_segment": top_seg.get("segment"),
                    "revenue": top_seg.get("total_revenue"),
                },
                evidence=summaries[:3],
                source_tools=["get_rfm_segment_summary"],
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                fallback_used=True,
            )

        # 2. Churn concentration / Churn risk inquiry
        if any(term in q_lower for term in ["churn", "risk", "at risk"]):
            raw = self.tools.get_churn_summary()
            churn_data = json.loads(raw)
            raw_segments = self.tools.get_rfm_segment_summary()
            seg_data = json.loads(raw_segments)
            ans = (
                f"There are currently {churn_data.get('high_risk_customers', 0)} customers classified as High Churn Risk "
                f"(average churn probability: {churn_data.get('average_churn_probability', 0) * 100:.1f}%). "
                f"The highest churn concentration is located in the 'At Risk' and 'About to Sleep' RFM segments."
            )
            return AgentAnalyticsResponse(
                request_id=req_id,
                question=question,
                answer=ans,
                intent="churn_risk_analysis",
                summary_metrics=churn_data,
                evidence=seg_data[:3],
                source_tools=["get_churn_summary", "get_rfm_segment_summary"],
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                fallback_used=True,
            )

        # 3. Top customers / Prioritize for retention inquiry
        if any(
            term in q_lower
            for term in ["top customer", "prioritize", "retention priority", "high risk customers"]
        ):
            raw_customers = self.tools.get_top_customers(limit=5)
            top_cust = json.loads(raw_customers)
            ans = (
                f"Retention efforts should prioritize high-value customers showing signs of dormancy. "
                f"Top customer spenders include: {', '.join([c.get('customer_id', '') for c in top_cust[:3]])}."
            )
            return AgentAnalyticsResponse(
                request_id=req_id,
                question=question,
                answer=ans,
                intent="retention_prioritization",
                summary_metrics={"top_customers_count": len(top_cust)},
                evidence=top_cust,
                source_tools=["get_top_customers"],
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                fallback_used=True,
            )

        # 4. Average order value (AOV) / Overview metrics inquiry
        if any(
            term in q_lower
            for term in [
                "average order value",
                "aov",
                "overview",
                "total revenue",
                "total customers",
            ]
        ):
            raw = self.tools.get_overview_metrics()
            metrics = json.loads(raw)
            ans = (
                f"The platform currently tracks {metrics.get('total_customers', 0):,} customers with "
                f"${metrics.get('total_gross_revenue', 0):,.2f} in total gross revenue. "
                f"The average revenue per customer is ${metrics.get('avg_revenue_per_customer', 0):,.2f} "
                f"with an average purchase frequency of {metrics.get('avg_order_frequency', 0)} orders."
            )
            return AgentAnalyticsResponse(
                request_id=req_id,
                question=question,
                answer=ans,
                intent="overview_metrics_query",
                summary_metrics=metrics,
                evidence=[metrics],
                source_tools=["get_overview_metrics"],
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                fallback_used=True,
            )

        # 5. Simulation inquiry
        if any(
            term in q_lower
            for term in ["simulation", "discount", "strategy", "campaign", "recovery"]
        ):
            raw_sim = self.tools.simulate_discount_strategy(discount_percentage=0.15)
            sim_data = json.loads(raw_sim)
            ans = (
                f"Simulating a 15% win-back discount strategy against eligible high-risk customers yields an "
                f"estimated net incremental value of ${sim_data.get('estimated_net_incremental_value', 0):,.2f} "
                f"(projected {sim_data.get('expected_retained_customers', 0)} retained customers against "
                f"${sim_data.get('total_cost', 0):,.2f} in total discount and outreach cost)."
            )
            return AgentAnalyticsResponse(
                request_id=req_id,
                question=question,
                answer=ans,
                intent="discount_simulation_query",
                summary_metrics={"net_value": sim_data.get("estimated_net_incremental_value")},
                evidence=[sim_data],
                source_tools=["simulate_discount_strategy"],
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                fallback_used=True,
            )

        # General Fallback
        raw_overview = self.tools.get_overview_metrics()
        overview = json.loads(raw_overview)
        ans = (
            f"Here is the high-level business analytics overview: "
            f"{overview.get('total_customers', 0):,} active customers, "
            f"${overview.get('total_gross_revenue', 0):,.2f} total revenue, "
            f"and {overview.get('high_risk_customers', 0)} high churn risk customers."
        )
        return AgentAnalyticsResponse(
            request_id=req_id,
            question=question,
            answer=ans,
            intent="general_analytics_fallback",
            summary_metrics=overview,
            evidence=[overview],
            source_tools=["get_overview_metrics"],
            warnings=[
                "No LLM provider configured. Deterministic analytics router answered question."
            ],
            latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
            fallback_used=True,
        )
