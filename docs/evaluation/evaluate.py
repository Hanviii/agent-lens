
import json
import sys
from pathlib import Path

# Allow importing the backend application from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.services.intent_parser import extract_intent


BENCHMARK_PATH = (
    PROJECT_ROOT / "evaluation" / "datasets" / "benchmark_questions.json"
)


def evaluate():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as file:
        benchmarks = json.load(file)

    total_checks = 0
    passed_checks = 0
    failed_cases = []

    print("\n" + "=" * 60)
    print("             AGENTLENS EVALUATION REPORT")
    print("=" * 60)

    for index, benchmark in enumerate(benchmarks, start=1):
        question = benchmark["question"]
        actual = extract_intent(question)

        checks = {
            "category": (
                benchmark.get("expected_category"),
                actual.get("category"),
            ),
            "max_price": (
                benchmark.get("max_price"),
                actual.get("max_price"),
            ),
            "min_price": (
                benchmark.get("min_price"),
                actual.get("min_price"),
            ),
            "min_rating": (
                benchmark.get("min_rating"),
                actual.get("min_rating"),
            ),
            "sort_by": (
                benchmark.get("sort_by"),
                actual.get("sort_by"),
            ),
        }

        if "rating_operator" in benchmark:
            checks["rating_operator"] = (
                benchmark["rating_operator"],
                actual.get("rating_operator"),
            )

        case_passed = True

        print(f"\nTest {index}: {question}")

        for field, (expected, observed) in checks.items():
            total_checks += 1
            passed = expected == observed

            if passed:
                passed_checks += 1
                status = "PASS"
            else:
                status = "FAIL"
                case_passed = False
                failed_cases.append(
                    {
                        "question": question,
                        "field": field,
                        "expected": expected,
                        "actual": observed,
                    }
                )

            print(
                f"  [{status}] {field}: "
                f"expected={expected!r}, actual={observed!r}"
            )

        print(f"  Result: {'PASS' if case_passed else 'FAIL'}")

    accuracy = (
        (passed_checks / total_checks) * 100
        if total_checks
        else 0
    )

    print("\n" + "=" * 60)
    print(f"Checks passed: {passed_checks}/{total_checks}")
    print(f"Field accuracy: {accuracy:.2f}%")
    print(f"Failed checks: {len(failed_cases)}")
    print("=" * 60)

    if failed_cases:
        print("\nFailures to fix:")
        for failure in failed_cases:
            print(
                f"- {failure['question']} | {failure['field']}: "
                f"expected {failure['expected']!r}, "
                f"got {failure['actual']!r}"
            )


if __name__ == "__main__":
    evaluate()
