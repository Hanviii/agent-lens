import json
from collections import Counter
from pathlib import Path

path = Path("data/cleaned_products.jsonl")

required = {
    "product_id", "title", "main_category", "categories",
    "store", "price", "currency", "average_rating",
    "rating_number", "features", "description", "details"
}

total = 0
ids = set()
duplicate_ids = 0
invalid_json = 0
missing_required = 0
invalid_prices = 0
invalid_ratings = 0
categories = Counter()
priced = 0
rated = 0

with path.open("r", encoding="utf-8") as file:
    for line in file:
        try:
            product = json.loads(line)
        except json.JSONDecodeError:
            invalid_json += 1
            continue

        total += 1

        if not required.issubset(product):
            missing_required += 1

        product_id = product.get("product_id")
        if not product_id:
            missing_required += 1
        elif product_id in ids:
            duplicate_ids += 1
        else:
            ids.add(product_id)

        price = product.get("price")
        if price is not None:
            if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
                invalid_prices += 1
            else:
                priced += 1

        rating = product.get("average_rating")
        if rating is not None:
            if (
                isinstance(rating, bool)
                or not isinstance(rating, (int, float))
                or not 0 <= rating <= 5
            ):
                invalid_ratings += 1
            else:
                rated += 1

        category = product.get("main_category") or "Uncategorized"
        categories[category] += 1

print("\n========== VALIDATION REPORT ==========")
print(f"Records: {total:,}")
print(f"Unique IDs: {len(ids):,}")
print(f"Duplicate IDs: {duplicate_ids}")
print(f"Invalid JSON lines: {invalid_json}")
print(f"Records missing required fields: {missing_required}")
print(f"Invalid non-null prices: {invalid_prices}")
print(f"Invalid non-null ratings: {invalid_ratings}")
print(f"Products with prices: {priced:,}")
print(f"Products with ratings: {rated:,}")

print("\nTop 15 main categories:")
for category, count in categories.most_common(15):
    print(f"  {category}: {count:,}")

print("\nFirst 2 cleaned records:")
with path.open("r", encoding="utf-8") as file:
    for _, line in zip(range(2), file):
        product = json.loads(line)
        print(json.dumps(product, ensure_ascii=False, indent=2)[:1800])
        print()

if (
    total != 10_000
    or invalid_json
    or duplicate_ids
    or missing_required
    or invalid_prices
    or invalid_ratings
):
    raise SystemExit("Validation failed. Review the report before importing.")

print("Validation passed.")
