
from time import perf_counter
from typing import Any

from neo4j import READ_ACCESS

from app.config import settings
from app.neo4j_client import get_driver
from app.services.cypher_validator import validate_cypher


MAX_RESULTS = 50
QUERY_TIMEOUT_SECONDS = 5


class QueryExecutionError(Exception):
    """Raised when a read-only product query cannot be executed."""


def execute_cypher(
    query: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Validate and execute a read-only Cypher query.

    Returns records as dictionaries and execution time in milliseconds.
    """
    valid, message = validate_cypher(query)

    if not valid:
        raise QueryExecutionError(f"Query rejected: {message}")

    safe_params = params or {}
    started = perf_counter()

    try:
        driver = get_driver()

        with driver.session(
            database=settings.neo4j_database,
            default_access_mode=READ_ACCESS,
        ) as session:
            result = session.run(
                query,
                parameters=safe_params,
                timeout=QUERY_TIMEOUT_SECONDS,
            )

            records = []
            for record in result:
                if len(records) >= MAX_RESULTS:
                    break
                records.append(record.data())

            result.consume()

        elapsed_ms = round((perf_counter() - started) * 1000, 2)

        return {
            "records": records,
            "count": len(records),
            "execution_time_ms": elapsed_ms,
        }


    except QueryExecutionError:
        raise
    except Exception as exc:
        print(
            f"AgentLens DB DEBUG: {type(exc).__name__}: {exc!r}"
        )
        raise QueryExecutionError(
            "The database query could not be completed."
        ) from exc
