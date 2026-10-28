
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.neo4j_client import get_driver

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("")
def get_products(
    search: Optional[str] = Query(default=None, max_length=200),
    category: Optional[str] = Query(default=None, max_length=100),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    min_rating: Optional[float] = Query(default=None, ge=0, le=5),
    limit: int = Query(default=12, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise HTTPException(
                status_code=400,
                detail="min_price cannot exceed max_price",
            )

    conditions = []
    params = {"limit": limit, "offset": offset}

    if search and search.strip():
        conditions.append(
            "(toLower(p.title) CONTAINS toLower($search) "
            "OR toLower(coalesce(p.description, '')) "
            "CONTAINS toLower($search))"
        )
        params["search"] = search.strip()

    if category and category.strip():
        conditions.append(
            "toLower(coalesce(p.main_category, '')) "
            "= toLower($category)"
        )
        params["category"] = category.strip()

    if min_price is not None:
        conditions.append("p.price IS NOT NULL AND p.price >= $min_price")
        params["min_price"] = min_price

    if max_price is not None:
        conditions.append("p.price IS NOT NULL AND p.price <= $max_price")
        params["max_price"] = max_price

    if min_rating is not None:
        conditions.append(
            "p.average_rating IS NOT NULL "
            "AND p.average_rating >= $min_rating"
        )
        params["min_rating"] = min_rating

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    count_query = f"""
    MATCH (p:Product)
    {where_clause}
    RETURN count(p) AS total
    """

    products_query = f"""
    MATCH (p:Product)
    {where_clause}
    RETURN p.product_id AS product_id,
           p.title AS title,
           p.main_category AS category,
           p.price AS price,
           p.average_rating AS rating,
           p.rating_number AS rating_count,
           p.store AS store,
           p.image_url AS image_url,
           p.description AS description
    ORDER BY p.average_rating DESC, p.title ASC
    SKIP $offset
    LIMIT $limit
    """

    try:
        driver = get_driver()

        with driver.session(database=settings.neo4j_database) as session:
            total = session.run(count_query, params).single()["total"]
            result = session.run(products_query, params)
            products = [record.data() for record in result]

        return {
            "status": "success",
            "total": total,
            "limit": limit,
            "offset": offset,
            "products": products,
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Product search is temporarily unavailable.",
        )
