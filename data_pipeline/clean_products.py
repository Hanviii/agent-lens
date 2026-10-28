import re
import gzip
import json
import random
from pathlib import Path

SOURCE = Path("data/meta_Electronics.jsonl.gz")
OUTPUT = Path("data/cleaned_products.jsonl")

TARGET_COUNT = 10_000
SEED = 42

# Broad category keywords for an electronics product-discovery project.
CORE_CATEGORIES = {
    "computers",
    "all electronics",
    "camera & photo",
    "cell phones & accessories",
    "home audio & theater",
    "portable audio & accessories",
    "gps & navigation",
    "amazon devices",
    "amazon fire tv",
    "apple products",
    "video games",
    "musical instruments",
    "fire phone",
}

CONDITIONAL_CATEGORIES = {
    "industrial & scientific",
    "tools & home improvement",
    "office products",
    "automotive",
    "car electronics",
    "amazon home",
    "appliances",
}

ELECTRONICS_TERMS = (
    "computer", "laptop", "tablet", "phone", "camera",
    "headphone", "earbud", "speaker", "television", "monitor",
    "keyboard", "mouse", "charger", "usb", "hdmi", "router",
    "network adapter", "graphics card", "hard drive", "ssd",
    "memory card", "micro sd", "bluetooth", "smartwatch",
    "gps", "webcam", "microphone", "projector", "dvd player",
    "electronic", "circuit board", "power supply",
)


def is_relevant_electronics(product):
    main_category = (
        product.get("main_category") or ""
    ).strip().casefold()

    title = (product.get("title") or "").casefold()

    if main_category in CORE_CATEGORIES:
        return True

    if main_category in CONDITIONAL_CATEGORIES:
        return any(term in title for term in ELECTRONICS_TERMS)

    return False


def clean_text(value):
    if isinstance(value, list):
        return [
            text
            for item in value
            if (text := clean_text(item))
        ]

    if value is None:
        return ""

    if isinstance(value, dict):
        return {
            str(key): clean_text(item)
            for key, item in value.items()
        }

    if isinstance(value, str):
        return " ".join(value.split())

    return value





def extract_image_url(raw):
    images = raw.get("images")

    if not isinstance(images, list):
        return None

    for image in images:
        if not isinstance(image, dict):
            continue

        for key in ("hi_res", "large", "thumb"):
            value = image.get(key)

            if not isinstance(value, str):
                continue

            # Extract the destination from Markdown: [text](URL)
            if "](" in value and ")" in value:
                url = value.split("](", 1)[1].split(")", 1)[0].strip()
            else:
                url = value.strip()

            url = url.replace(r"\\_", "_")

            if url.startswith(("https://", "http://")):
                return url

    return None


def clean_product(raw):
    product_id = str(raw.get("parent_asin") or "").strip()
    title = clean_text(raw.get("title"))

    if not product_id or not isinstance(title, str) or not title:
        return None

    categories = raw.get("categories")
    if not isinstance(categories, list):
        categories = []

    categories = [
        text for item in categories
        if (text := clean_text(item))
    ]

    features = raw.get("features")
    if not isinstance(features, list):
        features = []

    features = [
        text for item in features
        if (text := clean_text(item))
    ]

    descriptions = raw.get("description")
    if not isinstance(descriptions, list):
        descriptions = []

    descriptions = [
        text for item in descriptions
        if (text := clean_text(item))
    ]

    details = raw.get("details")
    if not isinstance(details, dict):
        details = {}

    price = raw.get("price")
    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or price < 0
    ):
        price = None

    rating = raw.get("average_rating")
    if (
        isinstance(rating, bool)
        or not isinstance(rating, (int, float))
        or not 0 <= rating <= 5
    ):
        rating = None

    rating_count = raw.get("rating_number")
    if (
        isinstance(rating_count, bool)
        or not isinstance(rating_count, int)
        or rating_count < 0
    ):
        rating_count = 0

    main_category = clean_text(raw.get("main_category"))

    product = {
        "product_id": product_id,
        "title": title,
        "main_category": main_category or "Uncategorized",
        "categories": categories,
        "store": clean_text(raw.get("store")) or None,
        "price": price,
        "currency": None,
        "average_rating": rating,
        "rating_number": rating_count,
        "features": features,
        "description": descriptions,
        "details": details,
        "image_url": extract_image_url(raw),
    }

    return product


def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Dataset not found: {SOURCE}")

    rng = random.Random(SEED)

    # Reservoir sampling bounds memory use.
    sample = []
    seen_ids = set()
    total_valid = 0
    relevant_count = 0
    skipped = 0

    with gzip.open(SOURCE, "rt", encoding="utf-8") as src:
        for line_number, line in enumerate(src, start=1):
            try:
                raw = json.loads(line)
                product = clean_product(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                skipped += 1
                continue

            if product is None or product["product_id"] in seen_ids:
                skipped += 1
                continue

            seen_ids.add(product["product_id"])
            total_valid += 1

            if not is_relevant_electronics(product):
                continue

            relevant_count += 1

            if len(sample) < TARGET_COUNT:
                sample.append(product)
            else:
                replacement = rng.randrange(relevant_count)
                if replacement < TARGET_COUNT:
                    sample[replacement] = product

            if total_valid % 100_000 == 0:
                print(f"Scanned {total_valid:,} valid unique products...")

    sample.sort(key=lambda product: product["product_id"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as dst:
        for product in sample:
            dst.write(json.dumps(product, ensure_ascii=False) + "\n")

    print("\n========== CLEANING REPORT ==========")
    print(f"Valid unique products scanned: {total_valid:,}")
    print(f"Relevant products found: {relevant_count:,}")
    print(f"Skipped records: {skipped:,}")
    print(f"Products exported: {len(sample):,}")
    print(f"Output file: {OUTPUT}")
    print(f"Output size: {OUTPUT.stat().st_size / (1024 * 1024):.2f} MiB")


if __name__ == "__main__":
    main()
