-- Initialise warehouse schema for the ISS astronauts pipeline

CREATE TABLE IF NOT EXISTS astronauts (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL,
    craft           VARCHAR(100)    NOT NULL,
    fetched_at      TIMESTAMP       NOT NULL,
    inserted_at     TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_astronaut_fetch UNIQUE (name, craft, fetched_at)
);

-- Track each pipeline run for observability
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              SERIAL PRIMARY KEY,
    dag_run_id      VARCHAR(255)    NOT NULL,
    people_in_space INT             NOT NULL,
    records_loaded  INT             NOT NULL,
    status          VARCHAR(50)     NOT NULL,
    run_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);
