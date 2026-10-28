
import re
from typing import Any


def extract_intent(question: str) -> dict[str, Any]:
    """Extract product-search intent from a natural-language question."""

    text = question.strip()
    lowered = text.lower()

    intent: dict[str, Any] = {
        "question": text,
        "keywords": [],
        "required_text_terms": [],
        "category": None,
        "product_type": None,
        "min_price": None,
        "max_price": None,
        "max_price_operator": "<=",
        "min_rating": None,
        "rating_operator": ">=",
        "sort_by": "relevance",
        "limit": 10,
    }

    # Extract requested result count.
    count_match = re.search(
        r"\b(?:show|find|list|top)\s+(\d{1,2})\b",
        lowered,
    )
    if count_match:
        intent["limit"] = max(1, min(int(count_match.group(1)), 50))

    # Extract rating before price to avoid confusing the two.
    rating_patterns = [
        r"\b(?:rated|rating(?:\s+of)?)\s+"
        r"(?:above|over|at least|greater than|more than|of)?\s*"
        r"(\d(?:\.\d+)?)\s*(?:\+?\s*)?(?:stars?|/\s*5)?\b",
        r"\b(\d(?:\.\d+)?)\s*(?:\+?\s*)?stars?\b",
    ]

    rating_match = None
    for pattern in rating_patterns:
        rating_match = re.search(pattern, lowered)
        if rating_match:
            break

    if rating_match:
        rating = float(rating_match.group(1))
        if 0 <= rating <= 5:
            intent["min_rating"] = rating

            rating_prefix = lowered[:rating_match.start()]
            rating_expression = lowered[
                rating_match.start():rating_match.end()
            ]
            if re.search(
                r"\b(?:above|over|greater than|more than)\b",
                rating_prefix + rating_expression,
            ):
                intent["rating_operator"] = ">"

    # Remove the rating expression before extracting price conditions.
    price_text = lowered
    if rating_match:
        price_text = (
            price_text[:rating_match.start()]
            + " "
            + price_text[rating_match.end():]
        )

    price_patterns = [
        (
            r"\b(?:under|below|less than|cheaper than|at most|up to)"
            r"\s*\$?\s*(\d+(?:\.\d+)?)\b",
            "max_price",
        ),
        (
            r"\b(?:over|above|more than|at least|greater than)"
            r"\s*\$?\s*(\d+(?:\.\d+)?)\b",
            "min_price",
        ),
    ]

    for pattern, field in price_patterns:
        match = re.search(pattern, price_text)
        if match:
            intent[field] = float(match.group(1))
            if field == "max_price":
                strict_terms = r"\b(?:under|below|less than|cheaper than)\b"
                intent["max_price_operator"] = (
                    "<" if re.search(strict_terms, match.group(0)) else "<="
                )

    # Identify the product category.
    categories = {
        "computers": [
            "computer", "computers", "laptop", "laptops",
            "desktop", "desktops", "pc",
        ],
        "phones": [
            "phone", "phones", "smartphone", "smartphones",
            "cell phone",
        ],
        "headphones": [
            "headphone", "headphones", "earbud", "earbuds",
            "earphone", "earphones",
        ],
        "keyboards": ["keyboard", "keyboards"],
        "cameras": ["camera", "cameras", "webcam", "webcams"],
        "speakers": ["speaker", "speakers"],
        "monitors": ["monitor", "monitors", "display"],
        "tablets": ["tablet", "tablets", "ipad"],
        "smartwatches": [
            "smartwatch", "smart watch", "fitness tracker",
        ],
        "chargers": ["charger", "chargers", "charging cable"],
    }

    padded_question = f" {lowered} "
    for category, terms in categories.items():
        if any(f" {term} " in padded_question for term in terms):
            intent["category"] = category
            break

    # Identify a specific product type within a broad category.
    if intent["category"] == "computers":
        if re.search(r"\b(?:laptops?|notebooks?)\b", lowered):
            intent["product_type"] = "laptop"
        elif re.search(r"\b(?:desktops?|desktop\s+pcs?)\b", lowered):
            intent["product_type"] = "desktop"
        elif re.search(r"\b(?:all[- ]in[- ]ones?)\b", lowered):
            intent["product_type"] = "all_in_one"

    # Detect sorting preference.
    if any(term in lowered for term in [
        "cheapest", "lowest price", "lowest priced",
        "price low to high", "increasing price",
        "budget", "affordable",
    ]):
        intent["sort_by"] = "price_asc"

    elif any(term in lowered for term in [
        "most expensive", "highest price", "highest priced",
        "price high to low", "decreasing price", "premium",
    ]):
        intent["sort_by"] = "price_desc"

    elif any(term in lowered for term in [
        "highest rated", "best rated", "top rated", "highly rated",
    ]):
        intent["sort_by"] = "rating_desc"

    # Use existing title/description text to verify ANC requests.
    if re.search(
        r"\banc\b|active noise cancellation|noise[- ]cancell?ing",
        lowered,
    ):
        intent["required_text_terms"] = [
            "anc",
            "active noise cancellation",
            "noise cancelling",
            "noise canceling",
        ]

    # Remove recognized filters and conversational filler.
    cleaned = lowered

    cleaned = re.sub(
        r"\b(?:active noise cancellation|noise[- ]cancell?ing|anc)\b",
        " ",
        cleaned,
    )

    if rating_match:
        cleaned = (
            cleaned[:rating_match.start()]
            + " "
            + cleaned[rating_match.end():]
        )

    cleaned = re.sub(
        r"\b(?:under|below|less than|cheaper than|at most|up to|"
        r"over|above|more than|at least|greater than)"
        r"\s*\$?\s*\d+(?:\.\d+)?\b",
        " ",
        cleaned,
    )

    cleaned = re.sub(
        r"\b(?:show|find|list|search|need|want|looking|look|"
        r"me|please|for|with|and|the|under|below|less than|"
        r"cheaper than|at most|up to|over|above|more than|"
        r"at least|greater than|dollars?|bucks?|products?|product|"
        r"highly rated|"
        r"a|an|in|on|of|"
        r"highest rated|best rated|top rated|cheapest|lowest price|"
        r"lowest priced|most expensive|highest price|highest priced|"
        r"price low to high|price high to low|increasing price|"
        r"decreasing price|affordable|budget|premium|rated|rating|"
        r"stars?|star)\b",
        " ",
        cleaned,
    )

    cleaned = re.sub(r"\b(?:i|i'm|im|i'd|id|i would|i want|i need)\b", " ", cleaned)
    cleaned = re.sub(r"^\s*\d{1,2}\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    intent["keywords"] = [cleaned] if cleaned else []

    return intent
