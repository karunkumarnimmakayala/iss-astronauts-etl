"""Validates and transforms raw astronaut API payload into clean records."""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def transform_astronauts(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Transform raw API payload into a list of clean astronaut records.

    Invalid records (missing name or craft) are logged and skipped.
    Returns a list of dicts with keys: name, craft, fetched_at.
    """
    people = raw.get("people", [])
    fetched_at = raw.get("fetched_at", datetime.now(timezone.utc).isoformat())
    records = []

    for person in people:
        name = person.get("name", "").strip()
        craft = person.get("craft", "").strip()

        if not name:
            logger.warning("Skipping record with missing name: %s", person)
            continue
        if not craft:
            logger.warning("Skipping record with missing craft: %s", person)
            continue

        records.append({
            "name": name.title(),
            "craft": craft.upper(),
            "fetched_at": fetched_at,
        })

    logger.info("Transformed %d valid records (of %d raw)", len(records), len(people))
    return records
