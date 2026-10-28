import gzip
import json
from collections import Counter

DATASET = "data/meta_Electronics.jsonl.gz"

total = 0
missing = Counter()
invalid = Counter()
categories = Counter()
main_categories = Counter()
ids = set()
duplicate_ids = 0
prices = 0
ratings = 0
stores = 0
feature_records = 0
description_records = 0
details_records = 0

with gzip.open(DATASET, "rt", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        try:
            product = json.loads(line)
        except json.JSONDecodeError:
            invalid["json"] += 1
            continue

        total += 1

        asin = product.get("parent_asin")
        if not asin:
            missing["parent_asin"] += 1
        elif asin in ids:
            duplicate_ids += 1
        else:
            ids.add(asin)

        for field in (
            "title", "main_category", "categories", "store",
            "average_rating", "rating_number", "price",
            "features", "description", "details"
        ):
            value = product.get(field)

            if value is None or value == "" or value == [] or value == {}:
                missing[field] += 1

        price = product.get("price")
        if isinstance(price, (int, float)) and price >= 0:
            prices += 1

        rating = product.get("average_rating")
        if isinstance(rating, (int, float)) and 0 <= rating <= 5:
            ratings += 1

        if product.get("store"):
            stores += 1

        if product.get("features"):
            feature_records += 1

        if product.get("description"):
            description_records += 1

        if product.get("details"):
            details_records += 1

        category = product.get("main_category")
        if category:
            main_categories[str(category)] += 1

        category_path = product.get("categories")
        if isinstance(category_path, list):
            for item in category_path:
                if item:
                    categories[str(item)] += 1

        if total % 100_000 == 0:
            print(f"Processed {total:,} records...")

print("\n========== DATASET REPORT ==========")
print(f"Valid JSON records: {total:,}")
print(f"Unique non-empty product IDs: {len(ids):,}")
print(f"Duplicate product IDs: {duplicate_ids:,}")
print(f"Invalid JSON lines: {invalid['json']:,}")

print("\nMissing or empty values:")
for field, count in missing.most_common():
    percentage = count / total * 100 if total else 0
    print(f"  {field}: {count:,} ({percentage:.2f}%)")

print("\nUseful field coverage:")
for label, count in (
    ("Numeric prices", prices),
    ("Valid numeric ratings", ratings),
    ("Store values", stores),
    ("Non-empty features", feature_records),
    ("Non-empty descriptions", description_records),
    ("Non-empty details", details_records),
):
    percentage = count / total * 100 if total else 0
    print(f"  {label}: {count:,} ({percentage:.2f}%)")

print("\nTop 15 main categories:")
for name, count in main_categories.most_common(15):
    print(f"  {name}: {count:,}")

print("\nTop 20 category labels:")
for name, count in categories.most_common(20):
    print(f"  {name}: {count:,}")
