from fastapi import APIRouter, HTTPException, Query, Request

from app.config import settings
from app.schemas import RecommendResponse, TextQuery

router = APIRouter(prefix="/api", tags=["recommendations"])


def _rec(request: Request):
    return request.app.state.recommender


@router.get("/health")
def health(request: Request):
    return {"status": "ok", **_rec(request).stats()}


@router.get("/categories")
def categories(request: Request):
    return _rec(request).categories()


@router.get("/products/search")
def search_products(request: Request, q: str = Query(..., min_length=2), limit: int = Query(8, le=25)):
    return _rec(request).find_products(q, limit)


@router.get("/products/random")
def random_products(request: Request, n: int = Query(6, ge=1, le=20)):
    return _rec(request).random_products(n)


@router.get("/recommend/{product_id}", response_model=RecommendResponse)
def recommend_by_id(request: Request, product_id: int,
                    top_n: int = Query(settings.default_top_n, ge=1, le=settings.max_top_n),
                    category: str | None = None):
    try:
        return _rec(request).recommend_by_id(product_id, top_n, category)
    except KeyError:
        raise HTTPException(404, f"Product id {product_id} not found")


@router.post("/recommend/text", response_model=RecommendResponse)
def recommend_by_text(request: Request, body: TextQuery):
    try:
        return _rec(request).recommend_by_text(body.text, body.top_n, body.category)
    except ValueError as e:
        raise HTTPException(422, str(e))
