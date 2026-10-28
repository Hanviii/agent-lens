
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.services.intent_parser import extract_intent
from app.services.cypher_generator import generate_cypher
from app.services.query_executor import execute_cypher
from app.services.response_formatter import format_response


CATEGORY_TERMS = {
    "keyboards": ["keyboard"],
    "headphones": ["headphone", "earbud", "earphone"],
    "computers": ["computer", "laptop", "desktop", " pc ", "pc "],
    "phones": ["phone", "smartphone", "cell phone"],
    "cameras": ["camera", "webcam"],
    "speakers": ["speaker"],
    "monitors": ["monitor", "display"],
    "tablets": ["tablet", "ipad"],
    "smartwatches": ["smartwatch", "smart watch", "fitness tracker"],
    "chargers": ["charger", "charging cable"],
}


def matches_category(title, category):
    """Check whether the product title matches the requested category."""
    title = f" {str(title or '').lower()} "
    terms = CATEGORY_TERMS.get(category)

    if not terms:
        return None

    return any(term in title for term in terms)


def check_price(product, benchmark):
    price = product.get("price")

    if benchmark.get("max_price") is not None:
        if price is None or price > benchmark["max_price"]:
            return False

    if benchmark.get("min_price") is not None:
        if price is None or price < benchmark["min_price"]:
            return False

    return True


def check_rating(product, benchmark, intent):
    minimum = benchmark.get("min_rating")

    if minimum is None:
        return True

    rating = product.get("rating")

    if rating is None:
        return False

    operator = benchmark.get(
        "rating_operator",
        intent.get("rating_operator", ">="),
    )

    if operator == ">":
        return rating > minimum

    return rating >= minimum


def check_sorting(products, sort_by):
    """Validate supported numeric sorting orders."""
    if sort_by == "price_asc":
        values = [p.get("price") for p in products]
        if any(value is None for value in values):
            return False
        return all(
            values[i] <= values[i + 1]
            for i in range(len(values) - 1)
        )

    if sort_by == "price_desc":
        values = [p.get("price") for p in products]
        if any(value is None for value in values):
            return False
        return all(
            values[i] >= values[i + 1]
            for i in range(len(values) - 1)
        )

    if sort_by == "rating_desc":
        values = [p.get("rating") for p in products]
        if any(value is None for value in values):
            return False
        return all(
            values[i] >= values[i + 1]
            for i in range(len(values) - 1)
        )

    # Relevance requires a separate relevance metric to verify.
    return None


def show_check(label, passed):
    if passed is None:
        print(f"  [SKIP] {label}: not independently measurable")
        return None

    print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
    return passed


def evaluate_products():
    import json

    benchmark_path = (
        PROJECT_ROOT
        / "evaluation"
        / "datasets"
        / "benchmark_questions.json"
    )

    with open(benchmark_path, encoding="utf-8") as file:
        benchmarks = json.load(file)

    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    skipped_checks = 0

    print("\n" + "=" * 65)
    print("           AGENTLENS PRODUCT-RESULT EVALUATION")
    print("=" * 65)

    for index, benchmark in enumerate(benchmarks, start=1):
        question = benchmark["question"]
        print(f"\nTest {index}: {question}")

        try:
            intent = extract_intent(question)
            cypher, params = generate_cypher(intent)
            result = execute_cypher(cypher, params)
            response = format_response(
                result["records"],
                result["execution_time_ms"],
            )
            products = response["products"]

        except Exception as exc:
            print(f"  [ERROR] Query could not be evaluated: {exc}")
            failed_checks += 1
            total_checks += 1
            continue

        print(f"  Products returned: {len(products)}")
        print(f"  Query time: {response['execution_time_ms']} ms")

        if not products:
            print("  [WARN] No products returned; retrieval needs review.")

        checks = []

        # Category correctness
        category = benchmark.get("expected_category")
        if category:
            category_results = [
                matches_category(p.get("title"), category)
                for p in products
            ]
            category_pass = (
                bool(products)
                and all(value is True for value in category_results)
            )
            checks.append(("Category correctness", category_pass))

        # Price constraints
        if (
            benchmark.get("max_price") is not None
            or benchmark.get("min_price") is not None
        ):
            price_pass = (
                bool(products)
                and all(check_price(p, benchmark) for p in products)
            )
            checks.append(("Price constraints", price_pass))

        # Rating constraints
        if benchmark.get("min_rating") is not None:
            rating_pass = (
                bool(products)
                and all(
                    check_rating(p, benchmark, intent)
                    for p in products
                )
            )
            checks.append(("Rating constraints", rating_pass))

        # Sorting constraints
        sort_by = benchmark.get("sort_by", "relevance")
        if sort_by in {"price_asc", "price_desc", "rating_desc"}:
            sorting_pass = (
                bool(products) and check_sorting(products, sort_by)
            )
            checks.append(("Sorting order", sorting_pass))
        elif sort_by == "relevance":
            checks.append(("Relevance order", None))

        for label, passed in checks:
            result_value = show_check(label, passed)

            if result_value is None:
                skipped_checks += 1
            else:
                total_checks += 1
                if result_value:
                    passed_checks += 1
                else:
                    failed_checks += 1

        # Show a few results for manual inspection.
        for product in products[:3]:
            print(
                f"    - {product.get('title')} | "
                f"price={product.get('price')} | "
                f"rating={product.get('rating')}"
            )

    print("\n" + "=" * 65)
    print("FINAL REPORT")
    print("=" * 65)
    print(f"Checks passed: {passed_checks}")
    print(f"Checks failed: {failed_checks}")
    print(f"Checks skipped: {skipped_checks}")
    print(f"Checks evaluated: {total_checks}")

    if total_checks:
        accuracy = passed_checks / total_checks * 100
        print(f"Constraint accuracy: {accuracy:.2f}%")

    print("=" * 65)


if __name__ == "__main__":
    evaluate_products()
