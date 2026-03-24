"""Loads transformed astronaut records into the PostgreSQL warehouse."""

from __future__ import annotations

import logging
import psycopg2
import psycopg2.extras
from typing import Any

logger = logging.getLogger(__name__)


def get_connection(conn_params: dict[str, Any]):
    return psycopg2.connect(**conn_params)


def load_astronauts(
    records: list[dict[str, Any]],
    conn_params: dict[str, Any],
    dag_run_id: str,
    people_in_space: int,
) -> int:
    """Insert astronaut records into the warehouse, skipping duplicates.

    Keyed on (name, craft, fetched_at) so re-runs are idempotent.
    Returns the number of rows actually inserted.
    """
    if not records:
        logger.warning("No records to load -- skipping insert")
        return 0

    insert_sql = """
        INSERT INTO astronauts (name, craft, fetched_at)
        VALUES (%(name)s, %(craft)s, %(fetched_at)s::timestamp)
        ON CONFLICT DO NOTHING
    """

    audit_sql = """
        INSERT INTO pipeline_runs (dag_run_id, people_in_space, records_loaded, status)
        VALUES (%s, %s, %s, %s)
    """

    rows_inserted = 0

    with get_connection(conn_params) as conn:
        with conn.cursor() as cur:
            for record in records:
                cur.execute(insert_sql, record)
                rows_inserted += cur.rowcount

            cur.execute(audit_sql, (dag_run_id, people_in_space, rows_inserted, "success"))
            conn.commit()

    logger.info("Loaded %d new rows into warehouse", rows_inserted)
    return rows_inserted
