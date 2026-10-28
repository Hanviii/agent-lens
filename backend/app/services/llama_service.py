
import json
import re

import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:3b"

ALLOWED_CATEGORIES = {
    "computers",
    "phones",
    "headphones",
    "keyboards",
    "cameras",
    "speakers",
    "monitors",
    "tablets",
    "smartwatches",
    "chargers",
}

ALLOWED_PRODUCT_TYPES = {
    "laptop",
    "desktop",
    "all_in_one",
}


def extract_intent_with_llama(query: str) -> dict:
    """Extract structured product filters using local Llama."""

    prompt = f"""
You extract search filters for an e-commerce product discovery app.

Do not search the web or database.
Do not generate Cypher or SQL.
Return JSON only.

Allowed categories:
{", ".join(sorted(ALLOWED_CATEGORIES))}

Rules:
- Laptops and desktops belong to computers.
- "above $300" means min_price = 300.
- "below $50" means max_price = 50.
- "rated 4 stars" means min_rating = 4 and rating_operator = ">=".
- "above 4 stars" means min_rating = 4 and rating_operator = ">".
- "at least 4 stars" means min_rating = 4 and rating_operator = ">=".
- Use null for unspecified values.
- product_type must be laptop, desktop, all_in_one, or null.
- rating_operator must be >=, >, <=, or <, or null.

Return exactly this JSON structure:
{{
  "category": null,
  "product_type": null,
  "min_price": null,
  "max_price": null,
  "min_rating": null,
  "rating_operator": null
}}

User query: {json.dumps(query)}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract product search intent. "
                        "Follow the requested JSON format exactly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=60,
    )

    response.raise_for_status()
    content = response.json()["message"]["content"]
    data = json.loads(content)

    # Validate the model's output before the application uses it.
    category = data.get("category")
    product_type = data.get("product_type")
    rating_operator = data.get("rating_operator")

    if category not in ALLOWED_CATEGORIES and category is not None:
        raise ValueError("Llama returned an unsupported category.")

    if product_type not in ALLOWED_PRODUCT_TYPES and product_type is not None:
        raise ValueError("Llama returned an unsupported product type.")

    if rating_operator not in {">=", ">", "<=", "<", None}:
        raise ValueError("Llama returned an invalid rating operator.")

    for field in ("min_price", "max_price", "min_rating"):
        value = data.get(field)

        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Invalid numeric filter: {field}")

            if value < 0:
                raise ValueError(f"Negative filter not allowed: {field}")

    if data.get("min_rating") is not None and data["min_rating"] > 5:
        raise ValueError("Rating cannot exceed 5.")

    # Keep product types consistent with the computer category.
    if product_type is not None and category != "computers":
        raise ValueError("Product type requires the computers category.")

    return data
