"""Fetches current astronaut data from the Open Notify ISS API."""

import logging
import requests
from datetime import datetime, timezone
from typing import Any

API_URL = "http://api.open-notify.org/astros.json"
TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)


def fetch_astronauts() -> dict[str, Any]:
    """Call the Open Notify API and return the raw payload with a fetched_at timestamp."""
    logger.info("Fetching astronaut data from %s", API_URL)

    response = requests.get(API_URL, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()

    payload = response.json()

    if payload.get("message") != "success":
        raise ValueError(f"Unexpected API message: {payload.get('message')}")
    if "people" not in payload or not isinstance(payload["people"], list):
        raise ValueError("Missing or malformed 'people' field in API response")

    payload["fetched_at"] = datetime.now(timezone.utc).isoformat()
    logger.info("Fetched %d astronauts successfully", payload["number"])

    return payload
