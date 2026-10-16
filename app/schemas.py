from pydantic import BaseModel, Field

from app.config import settings


class TextQuery(BaseModel):
    text: str = Field(..., min_length=1, examples=["men's black running shoes"])
    top_n: int = Field(settings.default_top_n, ge=1, le=settings.max_top_n)
    category: str | None = None


class Product(BaseModel):
    product_id: int
    name: str
    main_category: str
    sub_category: str
    image: str = ""
    link: str = ""
    ratings: str = ""
    discount_price: str = ""
    actual_price: str = ""


class Recommendation(Product):
    similarity: float


class RecommendResponse(BaseModel):
    query: dict
    results: list[Recommendation]
