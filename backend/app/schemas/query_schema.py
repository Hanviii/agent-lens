
from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language product discovery question",
    )


class QueryResponse(BaseModel):
    status: str
    answer: str
    products: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
