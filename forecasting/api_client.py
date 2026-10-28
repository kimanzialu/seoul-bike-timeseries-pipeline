"""
Client for the Task 3 FastAPI service.

It uses only the time-series endpoints that both backends provide:
    GET {prefix}/latest                        newest record
    GET {prefix}/range?start=...&end=...       records in a timestamp range
where prefix is /api/bikes (MySQL) or /api/mongo/bikes (MongoDB).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import httpx

SOURCES = {
    "sql": "/api/bikes",
    "mongo": "/api/mongo/bikes",
}


class ApiError(RuntimeError):
    """Raised when the API can't be reached or returns an unexpected response."""


class BikeApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", source: str = "sql",
                 timeout: float = 30.0, client: httpx.Client | None = None):
        if source not in SOURCES:
            raise ValueError(f"source must be one of {list(SOURCES)}")
        self.source = source
        self.prefix = SOURCES[source]
        # An injected client (e.g. FastAPI's TestClient) lets the tests run the
        # full pipeline without starting a server.
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)

    def _get(self, path: str, params: dict | None = None):
        try:
            response = self._client.get(self.prefix + path, params=params)
        except httpx.HTTPError as exc:
            raise ApiError(
                f"Could not reach the API ({exc}). Is it running? "
                "Start it with: uvicorn app.main:app --reload"
            ) from exc
        if response.status_code == 404:
            raise ApiError(f"GET {self.prefix}{path}: no records found (404).")
        if response.status_code >= 400:
            raise ApiError(f"GET {self.prefix}{path} failed: "
                           f"{response.status_code} {response.text[:200]}")
        return response.json()

    def get_latest(self) -> dict:
        """Return the newest record."""
        return self._get("/latest")

    def get_range(self, start: datetime, end: datetime) -> list[dict]:
        """Return all records with start <= timestamp <= end, oldest first."""
        return self._get("/range", params={"start": start.isoformat(),
                                           "end": end.isoformat()})

    def get_history(self, hours: int, end: datetime | None = None) -> list[dict]:
        """
        Return the ``hours`` hourly records ending at ``end``. If ``end`` is
        omitted, the history ends at the latest record in the database.
        """
        if end is None:
            end = datetime.fromisoformat(self.get_latest()["timestamp"])
        start = end - timedelta(hours=hours - 1)
        return self.get_range(start, end)

    def close(self):
        self._client.close()
