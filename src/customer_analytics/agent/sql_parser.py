"""SQL AST parsing and security inspection using sqlglot."""

import logging
from typing import Set, Tuple

import sqlglot
from sqlglot import exp

from customer_analytics.exceptions import UnsafeSQLException

logger = logging.getLogger(__name__)

# Forbidden expression types
FORBIDDEN_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,
    exp.Pragma,
    exp.Set,
)

FORBIDDEN_KEYWORDS = {
    "pragma",
    "attach",
    "detach",
    "vacuum",
    "reindex",
    "sqlite_master",
    "sqlite_schema",
    "sqlite_temp_master",
    "information_schema",
    "pg_catalog",
    "pg_tables",
    "pg_user",
    "into outfile",
    "load_file",
}


def parse_and_validate_sql(sql: str) -> Tuple[exp.Expression, Set[str]]:
    """Parse raw SQL query into AST, verify single-statement SELECT, and extract referenced table names."""
    if not sql or not sql.strip():
        raise UnsafeSQLException("Empty SQL query submitted.")

    cleaned_sql = sql.strip().rstrip(";")

    # Check for forbidden keywords in raw text as defense-in-depth
    lower_sql = cleaned_sql.lower()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in lower_sql:
            raise UnsafeSQLException(
                f"SQL contains prohibited keyword or catalog access: '{kw}'",
                details={"forbidden_token": kw},
            )

    # Reject comments that could conceal or bypass tokens
    if "--" in cleaned_sql or "/*" in cleaned_sql:
        raise UnsafeSQLException("SQL comments are not permitted in agent queries.")

    # Parse using sqlglot
    try:
        statements = sqlglot.parse(cleaned_sql)
    except Exception as e:
        raise UnsafeSQLException(f"Failed to parse SQL query: {str(e)}") from e

    if not statements or len(statements) == 0:
        raise UnsafeSQLException("No valid SQL statement found.")

    if len(statements) > 1:
        raise UnsafeSQLException(
            "Multiple statements (stacked queries) are strictly prohibited.",
            details={"statement_count": len(statements)},
        )

    stmt = statements[0]
    if stmt is None:
        raise UnsafeSQLException("Null statement parsed.")

    # Statement MUST be a SELECT query
    if not isinstance(stmt, exp.Select):
        raise UnsafeSQLException(
            f"Only read-only SELECT queries are allowed. Received: {stmt.key.upper()}",
            details={"statement_type": stmt.key},
        )

    # Check for any forbidden AST nodes in the entire syntax tree
    for node in stmt.walk():
        if isinstance(node, FORBIDDEN_EXPRESSION_TYPES):
            raise UnsafeSQLException(
                f"Prohibited SQL expression detected in query tree: {type(node).__name__}"
            )
        # Prevent SELECT ... INTO ...
        if isinstance(node, exp.Into):
            raise UnsafeSQLException("SELECT ... INTO writes are strictly forbidden.")

    # Extract all referenced tables across SELECT, FROM, JOINs, CTEs, and subqueries
    tables: Set[str] = set()
    for table_node in stmt.find_all(exp.Table):
        table_name = table_node.name.lower()
        if table_name:
            tables.add(table_name)

    return stmt, tables
