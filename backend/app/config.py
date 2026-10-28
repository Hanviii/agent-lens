
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from backend/.env
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

# Configure Python's trusted CA bundle for secure Neo4j connections.
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())


class Settings:
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "").strip()
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "").strip()
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j").strip()

    def validate(self):
        missing = []

        if not self.neo4j_uri:
            missing.append("NEO4J_URI")
        if not self.neo4j_username:
            missing.append("NEO4J_USERNAME")
        if not self.neo4j_password:
            missing.append("NEO4J_PASSWORD")

        if missing:
            raise RuntimeError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + ". Check backend/.env."
            )


settings = Settings()
