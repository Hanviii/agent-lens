
from neo4j import GraphDatabase

from app.config import settings

_driver = None


def get_driver():
    """Create the Neo4j driver once and reuse it."""
    global _driver

    if _driver is None:
        settings.validate()

        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password,
            ),
            connection_timeout=15,
            max_connection_pool_size=20,
        )

    return _driver


def verify_connection():
    """Verify credentials and connectivity to Neo4j AuraDB."""
    driver = get_driver()
    driver.verify_connectivity()

    with driver.session(database=settings.neo4j_database) as session:
        result = session.run(
            "RETURN 1 AS connection_ok, "
            "datetime() AS checked_at"
        )
        record = result.single()

        return {
            "connected": record["connection_ok"] == 1,
            "checked_at": str(record["checked_at"]),
        }


def close_driver():
    """Close the driver when the application shuts down."""
    global _driver

    if _driver is not None:
        _driver.close()
        _driver = None
