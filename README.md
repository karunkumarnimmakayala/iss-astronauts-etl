# ISS Astronauts ETL Pipeline

A production-style ETL pipeline that ingests live data from the [Open Notify ISS API](http://api.open-notify.org/astros.json), transforms and validates the records, and loads them into a PostgreSQL data warehouse — orchestrated with Apache Airflow and fully containerised with Docker.

---

## Architecture

```
┌─────────────────────┐     HTTP GET      ┌──────────────────────┐
│  Open Notify API    │ ────────────────► │  Extract (Python)    │
│  api.open-notify.org│                   │  scripts/extract.py  │
└─────────────────────┘                   └──────────┬───────────┘
                                                      │ raw payload (XCom)
                                                      ▼
                                          ┌──────────────────────┐
                                          │  Transform (Python)  │
                                          │  scripts/transform.py│
                                          │  - Validate fields   │
                                          │  - Clean strings     │
                                          └──────────┬───────────┘
                                                      │ clean records (XCom)
                                                      ▼
                                          ┌──────────────────────┐
                                          │  Load (Python)       │
                                          │  scripts/load.py     │
                                          │  - Idempotent insert │
                                          │  - Audit log         │
                                          └──────────┬───────────┘
                                                      │
                                                      ▼
                                          ┌──────────────────────┐
                                          │  PostgreSQL          │
                                          │  Warehouse           │
                                          │  - astronauts        │
                                          │  - pipeline_runs     │
                                          └──────────────────────┘

All tasks orchestrated by Apache Airflow (daily @ 07:00 UTC)
```

---

## Project Structure

```
etl_pipeline/
├── dags/
│   └── iss_astronauts_etl.py   # Airflow DAG definition
├── scripts/
│   ├── extract.py              # API ingestion
│   ├── transform.py            # Validation & cleaning
│   └── load.py                 # PostgreSQL loader
├── sql/
│   └── init.sql                # Warehouse schema
├── tests/
│   └── test_pipeline.py        # Unit tests (pytest)
├── docker-compose.yml          # Airflow + PostgreSQL services
├── requirements.txt
└── README.md
```

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/etl-pipeline-iss.git
cd etl-pipeline-iss
```

### 2. Start all services

```bash
docker compose up -d
```

This starts:
- `postgres-airflow` — Airflow metadata database (internal)
- `postgres-warehouse` — Data warehouse on port `5433`
- `airflow-init` — Runs DB migrations and creates admin user
- `airflow-webserver` — Airflow UI on port `8080`
- `airflow-scheduler` — Triggers DAG runs on schedule

### 3. Open Airflow UI

Navigate to [http://localhost:8080](http://localhost:8080)

```
Username: admin
Password: admin
```

### 4. Trigger the DAG

Find `iss_astronauts_etl` in the DAG list and click the **play button** to trigger a manual run, or wait for the daily schedule (07:00 UTC).

### 5. Query the warehouse

```bash
docker exec -it etl_pipeline-postgres-warehouse-1 \
  psql -U warehouse -d warehouse -c "SELECT * FROM astronauts ORDER BY inserted_at DESC;"
```

```bash
docker exec -it etl_pipeline-postgres-warehouse-1 \
  psql -U warehouse -d warehouse -c "SELECT * FROM pipeline_runs ORDER BY run_at DESC;"
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Pipeline Design Decisions

| Decision | Reason |
|---|---|
| **XCom for inter-task data** | Keeps tasks decoupled; each task has a single responsibility |
| **Idempotent inserts** (`ON CONFLICT DO NOTHING`) | Re-running the DAG for the same date never creates duplicates |
| **`pipeline_runs` audit table** | Provides observability — every run is logged with record count and status |
| **Validation in transform layer** | Bad records are skipped with a warning rather than crashing the pipeline |
| **Retries: 3 × 5 min** | Handles transient API or network failures gracefully |
| **`catchup=False`** | Prevents Airflow from back-filling historical runs on first deploy |

---

## Data Model

### `astronauts`
| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment surrogate key |
| `name` | VARCHAR(255) | Astronaut full name (title-cased) |
| `craft` | VARCHAR(100) | Spacecraft name (upper-cased) |
| `fetched_at` | TIMESTAMP | When the API was called |
| `inserted_at` | TIMESTAMP | When the row was inserted |

### `pipeline_runs`
| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment |
| `dag_run_id` | VARCHAR(255) | Airflow run identifier |
| `people_in_space` | INT | Raw count from API |
| `records_loaded` | INT | Rows actually inserted |
| `status` | VARCHAR(50) | `success` / `failed` |
| `run_at` | TIMESTAMP | Pipeline execution time |

---

## Tech Stack

- **Python 3.11** — ETL logic
- **Apache Airflow 2.8** — Orchestration & scheduling
- **PostgreSQL 15** — Data warehouse
- **Docker Compose** — Local development environment
- **pytest** — Unit testing
