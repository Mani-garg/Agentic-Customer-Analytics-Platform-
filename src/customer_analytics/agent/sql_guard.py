"""SQL security guardrail module orchestrating parsing, allow-listing, and execution bounds."""

import logging
from typing import Optional, Set

from customer_analytics.agent.allowlist import SQLAllowList
from customer_analytics.agent.sql_parser import parse_and_validate_sql
from customer_analytics.config import get_settings
from customer_analytics.exceptions import UnsafeSQLException

logger = logging.getLogger(__name__)


class SQLGuard:
    """Multi-tiered validator enforcing read-only constraints, table allow-lists, and row limits."""

    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        max_query_length: int = 1000,
        max_rows: int = 100,
    ):
        settings = get_settings()
        self.allowed_tables = allowed_tables or settings.sql_allowed_tables
        self.allow_list = SQLAllowList(self.allowed_tables)
        self.max_query_length = max_query_length or settings.sql_max_query_length
        self.max_rows = max_rows or settings.sql_max_rows

    def validate_and_sanitize(self, sql: str) -> str:
        """Validate raw SQL against all guardrails and return sanitized SQL with guaranteed LIMIT."""
        if not sql:
            raise UnsafeSQLException("SQL query is empty.")

        if len(sql) > self.max_query_length:
            raise UnsafeSQLException(
                f"SQL query exceeds maximum permitted character length ({len(sql)} > {self.max_query_length}).",
                details={"query_length": len(sql), "max_permitted": self.max_query_length},
            )

        # 1. Parse AST and check forbidden operations
        stmt, referenced_tables = parse_and_validate_sql(sql)

        # 2. Enforce table allow-list
        self.allow_list.validate_tables(referenced_tables)

        # 3. Enforce / inject LIMIT clause
        current_limit = stmt.args.get("limit")
        if current_limit is None:
            stmt = stmt.limit(self.max_rows)
        else:
            try:
                # Extract numeric limit value across sqlglot dialect versions
                limit_node = (
                    current_limit.expression
                    if hasattr(current_limit, "expression") and current_limit.expression is not None
                    else current_limit.this
                )
                limit_val = int(limit_node.sql())
                if limit_val > self.max_rows or limit_val <= 0:
                    stmt = stmt.limit(self.max_rows)
            except Exception:
                stmt = stmt.limit(self.max_rows)

        sanitized_sql = stmt.sql()
        logger.info(f"SQL Guard accepted query referencing {referenced_tables}: {sanitized_sql}")
        return sanitized_sql
