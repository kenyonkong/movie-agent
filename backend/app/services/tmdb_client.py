import gzip
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from app.core.config import settings

class TMDBClient:
    """
    Small TMDB API client for dataset ingestion.

    This client is intentionally simple:
    - downloads daily movie ID exports
    - fetches movie details
    - appends credits and keywords in the same request
    - handles basic retry and 429 rate-limit responses
    """

    API_BASE_URL = "https://api.themoviedb.org/3"
    EXPORT_BASE_URL = "https://files.tmdb.org/p/exports"

    def __init__(self) -> None:
        if not settings.tmdb_api_read_access_token:
            raise ValueError("TMDb API read access token is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {settings.tmdb_api_read_access_token}",
            "Content-Type": "application/json"
        })
    

    def download_recent_movie_id_export(
        self, 
        output_dir: Path, 
        lookback_days: int = 7
    ) -> Path:
        """
        Download the most recent available TMDB movie ID export.

        TMDB daily export files are only ID/high-level metadata seeds.
        They are not full movie metadata, so we use them to decide which
        movie detail endpoints to call.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now(timezone.utc).date()

        last_error: Exception | None = None

        for offset in range(lookback_days):
            date = today - timedelta(days=offset)
            filename = f"movie_ids_{date.month:02d}_{date.day:02d}_{date.year}.json.gz"
            url = f"{self.EXPORT_BASE_URL}/{filename}"
            output_path = output_dir / filename

            try:
                response = self.session.get(url, timeout=60)

                if response.status_code == 200:
                    output_path.write_bytes(response.content)
                    print(f"Downloaded TMDB ID export: {filename}")
                    return output_path
                
                last_error = RuntimeError(
                    f"Failed {filename}: status={response.status_code}"
                )
            
            except Exception as error:
                last_error = error

        raise RuntimeError(
            f"Could not download a recent TMDB movie ID export. Last error: {last_error}"
        )

    
    def read_movie_id_export(
        self, 
        export_path: Path, 
    ) -> list[dict[str, Any]]:
        """
        Read a gzipped TMDB export file.

        Each line is a JSON object.
        """
        rows: list[dict[str, Any]] = []

        with gzip.open(export_path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))

        return rows
    

    def get_movie_details(
        self, 
        movie_id: int, 
        retries: int = 3
    ) -> dict[str, Any] | None:
        """
        Fetch full movie details from TMDB.

        append_to_response lets us fetch credits and keywords together with
        movie details instead of making separate requests.
        """
        url = f"{self.API_BASE_URL}/movie/{movie_id}"

        params = {
            "language": settings.tmdb_language, 
            "append_to_response": "credits,keywords"
        }

        for attempt in range(retries):
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                time.sleep(settings.tmdb_request_sleep_seconds)
                return response.json()

            if response.status_code == 404:
                print(f"Movie not found: {movie_id}")
                return None
        
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "2"))
                time.sleep(retry_after)
                continue

            if response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue

            print(
                f"Skipping movie_id={movie_id}: "
                f"status={response.status_code}, body={response.text[:200]}"
            )
            return None

        print(f"Failed movie_id={movie_id} after {retries} retries.")
        return None