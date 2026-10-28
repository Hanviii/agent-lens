
from time import perf_counter

from fastapi import APIRouter, HTTPException

from app.schemas.query_schema import QueryRequest, QueryResponse
from app.services.intent_parser import extract_intent
from app.services.llama_service import extract_intent_with_llama
from app.services.cypher_generator import generate_cypher
from app.services.query_executor import (
    execute_cypher,
    QueryExecutionError,
)
from app.services.response_formatter import format_response

router = APIRouter(prefix="/api", tags=["Query"])


@router.post("/query", response_model=QueryResponse)
def query_products(request: QueryRequest):
    started = perf_counter()

    try:
        # Parse deterministic filters from the user's original question.
        rule_intent = extract_intent(request.question)

        # Try Llama for additional category/product-type interpretation.
        try:
            llama_intent = extract_intent_with_llama(request.question)
            print("AgentLens: using merged Llama and rule-based intent")
        except Exception as exc:
            print(
                "AgentLens: Llama extraction failed; "
                f"using rule-based fallback ({type(exc).__name__})"
            )
            llama_intent = {}

        # Start with rule-based fields: keywords, feature requirements,
        # strict price operators and deterministic filter extraction.
        intent = dict(rule_intent)

        # Prefer Llama's valid category/type when it provides one.
        if llama_intent.get("category") is not None:
            intent["category"] = llama_intent["category"]

        if llama_intent.get("product_type") is not None:
            intent["product_type"] = llama_intent["product_type"]

        # Use rule-based numeric filters when recognized; otherwise,
        # retain Llama's extracted values.
        for field in ("min_price", "max_price", "min_rating"):
            if rule_intent.get(field) is None and llama_intent.get(field) is not None:
                intent[field] = llama_intent[field]

        # Only apply rule-based operators when their corresponding
        # constraints were recognized by the rule-based parser.
        if rule_intent.get("min_rating") is None:
            intent["rating_operator"] = (
                llama_intent.get("rating_operator") or ">="
            )

        if rule_intent.get("max_price") is None:
            intent["max_price_operator"] = "<="

        cypher, params = generate_cypher(intent)
        print("DEBUG category:", intent.get("category"))
        print("DEBUG max price operator:", intent.get("max_price_operator"))
        print("DEBUG rating operator:", intent.get("rating_operator"))
        print("DEBUG feature terms:", intent.get("required_text_terms", []))
        print("DEBUG generated query:", cypher)
        result = execute_cypher(cypher, params)

        response = format_response(
            result["records"],
            result["execution_time_ms"],
        )

        response["execution_time_ms"] = round(
            (perf_counter() - started) * 1000,
            2,
        )

        return response

    except QueryExecutionError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Log the exception server-side without exposing internals.
        print(
            f"AgentLens query error: {type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process your product search. "
                "Please try again."
            ),
        ) from exc
