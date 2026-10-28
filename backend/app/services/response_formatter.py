
from typing import Any


def format_response(
    records: list[dict[str, Any]],
    execution_time_ms: float,
) -> dict[str, Any]:
    """Format database records into a frontend-friendly response."""

    products = []

    for record in records:
        products.append({
            "product_id": record.get("product_id"),
            "title": record.get("title") or "Untitled product",
            "category": record.get("category"),
            "price": record.get("price"),
            "rating": record.get("rating"),
            "rating_count": record.get("rating_count"),
            "store": record.get("store"),
            "image_url": record.get("image_url"),
            "description": record.get("description"),
        })

    count = len(products)

    if count == 0:
        answer = (
            "No matching products were found. "
            "Try changing your search or relaxing your filters."
        )
    elif count == 1:
        answer = "Found 1 matching product."
    else:
        answer = f"Found {count} matching products."

    return {
        "status": "success",
        "answer": answer,
        "products": products,
        "count": count,
        "execution_time_ms": round(execution_time_ms, 2),
        "error": None,
    }
