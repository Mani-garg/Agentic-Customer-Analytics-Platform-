"""Table allow-list verification and schema inspection controls."""

from typing import Iterable, Set

from customer_analytics.exceptions import UnsafeSQLException


class SQLAllowList:
    """Enforces that all queried tables and views reside in an approved allow-list."""

    def __init__(self, allowed_tables: Iterable[str]):
        self.allowed_tables: Set[str] = {t.strip().lower() for t in allowed_tables if t.strip()}

    def validate_tables(self, referenced_tables: Set[str]) -> None:
        """Verify that every referenced table is explicitly permitted."""
        if not referenced_tables:
            # e.g., SELECT 1; or function call without tables
            return

        unauthorized = referenced_tables - self.allowed_tables
        if unauthorized:
            raise UnsafeSQLException(
                f"Access denied to unauthorized table(s): {sorted(list(unauthorized))}. "
                f"Permitted tables: {sorted(list(self.allowed_tables))}",
                details={
                    "unauthorized_tables": list(unauthorized),
                    "allowed_tables": list(self.allowed_tables),
                },
            )
