
import json
import os
import sys
from pathlib import Path

from neo4j import GraphDatabase
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
DATA_FILE = PROJECT_ROOT / "data" / "cleaned_products.jsonl"

load_dotenv(BACKEND_DIR / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "").strip()
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "").strip()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "").strip()

BATCH_SIZE = 500

# Keep only fields that are useful and predictable for our graph.
def normalize_product(raw):
    product_id = raw.get("parent_asin") or raw.get("product_id") or raw.get("asin")
    title = raw.get("title")

    if not product_id or not title:
        return None

    def clean_text(value):
        if isinstance(value, list):
            return " ".join(str(item) for item in value if item)
        if value is None:
            return None
        return str(value).strip() or None

    price = raw.get("price")
    rating = raw.get("average_rating")
    rating_count = raw.get("rating_number")

    try:
        price = float(price) if price not in (None, "") else None
    except (TypeError, ValueError):
        price = None

    try:
        rating = float(rating) if rating not in (None, "") else None
    except (TypeError, ValueError):
        rating = None

    try:
        rating_count = int(rating_count) if rating_count not in (None, "") else None
    except (TypeError, ValueError):
        rating_count = None

    return {
        "product_id": str(product_id).strip(),
        "title": str(title).strip(),
        "main_category": clean_text(raw.get("main_category")),
        "price": price,
        "average_rating": rating,
        "rating_number": rating_count,
        "store": clean_text(raw.get("store")),
        "features": clean_text(raw.get("features")),
        "description": clean_text(raw.get("description")),
        "image_url": (
            raw.get("images", [{}])[0].get("hi_res")
            or raw.get("images", [{}])[0].get("large")
            or raw.get("images", [{}])[0].get("thumb")
            if isinstance(raw.get("images"), list)
            and raw.get("images")
            and isinstance(raw.get("images")[0], dict)
            else None
        ),
    }


def read_batches(path, batch_size):
    batch = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {exc}"
                ) from exc

            product = normalize_product(raw)
            if product:
                batch.append(product)

            if len(batch) >= batch_size:
                yield batch
                batch = []

    if batch:
        yield batch


def import_batch(session, batch):
    query = """
    UNWIND $products AS item
    MERGE (p:Product {product_id: item.product_id})
    SET p.title = item.title,
        p.main_category = item.main_category,
        p.price = item.price,
        p.average_rating = item.average_rating,
        p.rating_number = item.rating_number,
        p.store = item.store,
        p.features = item.features,
        p.description = item.description,
        p.image_url = item.image_url
    WITH p, item
    FOREACH (_ IN CASE
        WHEN item.main_category IS NOT NULL AND item.main_category <> ''
        THEN [1] ELSE [] END |
        MERGE (c:Category {name: item.main_category})
        MERGE (p)-[:BELONGS_TO]->(c)
    )
    RETURN count(p) AS processed
    """
    result = session.run(query, products=batch)
    return result.single()["processed"]


def main():
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE]):
        sys.exit(
            "Missing Neo4j settings. Check backend/.env without sharing its contents."
        )

    if not DATA_FILE.exists():
        sys.exit(f"Dataset not found: {DATA_FILE}")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        connection_timeout=15,
        max_connection_pool_size=10,
    )

    total = 0
    batch_number = 0

    try:
        driver.verify_connectivity()

        with driver.session(database=NEO4J_DATABASE) as session:
            for batch in read_batches(DATA_FILE, BATCH_SIZE):
                batch_number += 1
                processed = import_batch(session, batch)
                total += processed
                print(
                    f"Batch {batch_number}: {processed} products processed "
                    f"(total: {total})"
                )

        print(f"\nImport complete. Products processed: {total}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
