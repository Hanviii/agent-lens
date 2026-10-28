
from fastapi import APIRouter
from app.neo4j_client import verify_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AgentLens API",
    }


@router.get("/health/neo4j")
def neo4j_health_check():
    try:
        result = verify_connection()
        return {
            "status": "ok" if result["connected"] else "error",
            "neo4j": result,
        }
    except Exception:
        return {
            "status": "error",
            "neo4j": {
                "connected": False,
                "message": "Database connection failed. Check the server logs.",
            },
        }
