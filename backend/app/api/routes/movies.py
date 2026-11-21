from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.db.schemas import MovieSearchResponse
from app.services.movie_catalog import MovieCatalogService

router = APIRouter(prefix="/movies", tags=["movies"])

movie_catalog = MovieCatalogService()


@router.get("/search", response_model=MovieSearchResponse)
def search_movies(
    q: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MovieSearchResponse:
    """Search the local movie catalog by title only."""
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="Movie title query cannot be blank.",
        )

    try:
        results, total = movie_catalog.search(
            query,
            limit=limit,
            offset=offset,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return MovieSearchResponse(
        query=query,
        total=total,
        limit=limit,
        offset=offset,
        results=results,
    )
