from pydantic import BaseModel, Field

class RecommendRequest(BaseModel):
    user_id: str = Field(
        default="demo_user",
        description="User ID used for personalization. For now, this can be demo_user.",
    )
    query: str = Field(
        ..., # Required field
        min_length=2,
        max_length=500,
        description="Natural-language movie preference query.",
    )
    top_k: int = Field(
        default=5, 
        ge=1,
        le=10,
        description="Number of movie recommendations to return.",
    )


class MovieRecommendation(BaseModel):
    movie_id: str
    title: str
    release_year: int | None = None
    genres: str | None = None
    score: float
    distance: float
    reason: str
    document_preview: str


class RecommendResponse(BaseModel):
    user_id: str
    query: str
    top_k: int
    results: list[MovieRecommendation]
    latency_ms: float