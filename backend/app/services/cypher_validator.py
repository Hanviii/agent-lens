
import re


FORBIDDEN_KEYWORDS = {
    "CREATE",
    "DELETE",
    "DETACH",
    "DROP",
    "MERGE",
    "REMOVE",
    "SET",
    "LOAD",
    "FOREACH",
    "GRANT",
    "DENY",
    "REVOKE",
    "ALTER",
    "RENAME",
    "TERMINATE",
    "STOP",
    "START",
    "USE",
    "CALL",
    "SHOW",
}

ALLOWED_START = re.compile(r"^\s*MATCH\b", re.IGNORECASE)


def validate_cypher(query: str) -> tuple[bool, str]:
    """
    Basic read-only Cypher validation.
    This is a defense-in-depth check, not a complete Cypher parser.
    """
    if not isinstance(query, str) or not query.strip():
        return False, "Query must be a non-empty string."

    if len(query) > 10_000:
        return False, "Query is too long."

    # Only allow a single statement.
    if ";" in query:
        return False, "Multiple statements are not allowed."

    # Reject comments to reduce opportunities to hide query fragments.
    if "//" in query or "/*" in query or "*/" in query:
        return False, "Comments are not allowed."

    if not ALLOWED_START.match(query):
        return False, "Only read-only MATCH queries are allowed."

    # Remove quoted strings before checking keywords, so a product title
    # containing words such as 'delete' doesn't cause a false rejection.
    scrubbed = re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"", " ", query)

    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", scrubbed)
    forbidden_found = FORBIDDEN_KEYWORDS.intersection(
        token.upper() for token in tokens
    )

    if forbidden_found:
        return False, (
            "Forbidden Cypher operation detected: "
            + ", ".join(sorted(forbidden_found))
        )

    if not re.search(r"\bRETURN\b", scrubbed, re.IGNORECASE):
        return False, "Query must contain RETURN."

    return True, "Query passed basic read-only checks."
