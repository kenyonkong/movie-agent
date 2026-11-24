import csv
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import movies
from app.services.movie_catalog import MovieCatalogService


def write_catalog(path: Path) -> None:
    fieldnames = [
        "id",
        "title",
        "release_year",
        "director",
        "cast_clean",
        "vote_average",
        "popularity",
        "poster_path",
        "backdrop_path",
    ]
    rows = [
        {
            "id": "10",
            "title": "Batman",
            "release_year": "1989",
            "director": "Tim Burton",
            "cast_clean": "Michael Keaton, Jack Nicholson",
            "vote_average": "7.2",
            "popularity": "10.0",
            "poster_path": "/batman.jpg",
            "backdrop_path": "/batman-bg.jpg",
        },
        {
            "id": "11",
            "title": "Batman Begins",
            "release_year": "2005",
            "director": "Christopher Nolan",
            "cast_clean": "Christian Bale, Michael Caine",
            "vote_average": "7.7",
            "popularity": "30.0",
            "poster_path": "begins.jpg",
            "backdrop_path": "",
        },
        {
            "id": "12",
            "title": "The Lego Batman Movie",
            "release_year": "2017",
            "director": "Chris McKay",
            "cast_clean": "Will Arnett",
            "vote_average": "7.2",
            "popularity": "20.0",
            "poster_path": "",
            "backdrop_path": "",
        },
        {
            "id": "13",
            "title": "Unrelated Movie",
            "release_year": "2020",
            "director": "Someone Else",
            "cast_clean": "Batman Jones",
            "vote_average": "8.0",
            "popularity": "100.0",
            "poster_path": "",
            "backdrop_path": "",
        },
    ]

    with path.open("w", encoding="utf-8", newline="") as catalog_file:
        writer = csv.DictWriter(catalog_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_search_matches_only_title_and_formats_metadata(
    tmp_path: Path,
) -> None:
    catalog_path = tmp_path / "movies.csv"
    write_catalog(catalog_path)
    service = MovieCatalogService(catalog_path)

    results, total = service.search("  BATMAN  ", limit=2)

    assert total == 3
    assert [movie.title for movie in results] == [
        "Batman Begins",
        "The Lego Batman Movie",
    ]
    assert results[0].director == "Christopher Nolan"
    assert results[0].cast == ["Christian Bale", "Michael Caine"]
    assert results[0].movie_rating == 7.7
    assert results[0].poster_url == (
        "https://image.tmdb.org/t/p/w500/begins.jpg"
    )
    assert results[0].backdrop_url is None
    assert all(movie.title != "Unrelated Movie" for movie in results)


def test_search_normalizes_punctuation_and_matches_partial_titles(tmp_path: Path) -> None:
    catalog_path = tmp_path / "movies.csv"
    catalog_path.write_text(
        "id,title,popularity\n1,Spider-Man: Homecoming,20\n2,The Amazing Spider-Man,10\n",
        encoding="utf-8",
    )
    service = MovieCatalogService(catalog_path)

    for query in ("spider man", "SPIDER  MAN", "spider–man", "spider m"):
        results, total = service.search(query)
        assert total == 2
        assert [movie.title for movie in results] == [
            "Spider-Man: Homecoming",
            "The Amazing Spider-Man",
        ]

    assert service.search("---") == ([], 0)


def test_search_supports_pagination(tmp_path: Path) -> None:
    catalog_path = tmp_path / "movies.csv"
    write_catalog(catalog_path)
    service = MovieCatalogService(catalog_path)

    results, total = service.search("batman", limit=1, offset=1)

    assert total == 3
    assert [movie.title for movie in results] == [
        "The Lego Batman Movie"
    ]


def test_movie_search_endpoint_returns_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    catalog_path = tmp_path / "movies.csv"
    write_catalog(catalog_path)
    monkeypatch.setattr(
        movies,
        "movie_catalog",
        MovieCatalogService(catalog_path),
    )
    app = FastAPI()
    app.include_router(movies.router)
    client = TestClient(app)

    response = client.get(
        "/movies/search",
        params={"q": "Batman", "limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "Batman"
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert len(body["results"]) == 2
