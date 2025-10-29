# 🚀 Crypto Dashboard (Portfolio-ready)

A cleaned, portfolio-ready copy of the Cryptocurrency Data Pipeline & Dashboard. This folder (crypto-dashboard-fixed/) contains the Streamlit dashboard, an ETL pipeline using PySpark, Dockerfiles, and helpers tuned for local development and demonstration.

This README focuses on accurate, step-by-step instructions for running the project locally using Docker Compose, a description of the architecture, and troubleshooting tips specific to the repo layout in this branch.

----

## Contents

- `app.py` — Streamlit dashboard (visualization & manual save-to-DB)  
- `crypto_pipeline.py` — ETL pipeline that extracts CoinGecko data, processes with Spark, writes to Postgres, and creates chart images  
- `pipeline_dag.py` — Airflow DAG wrapper that invokes the pipeline  
- `docker-compose.yml` (root of repo) — brings up Postgres, Streamlit app, pgAdmin, and Airflow services  
- `init.sql` (root) — Postgres initialization SQL (creates `crypto_prices` table and sample rows)  
- `crypto-dashboard-fixed/` — this folder (cleaned-up files for portfolio)  
  - `.env.example` — example environment variables  
  - `requirements-app.txt` — app dependencies (Streamlit + libs)  
  - `requirements-airflow.txt` — minimal runtime deps for Airflow images  
  - `Dockerfile` — app image (uses `requirements-app.txt`)  
  - `Dockerfile.airflow` — Airflow image tweaks (installs `requirements-airflow.txt` only)  
  - `LICENSE` — MIT license  
  - `.gitignore`

----

## Architecture (high level)

CoinGecko API → PySpark processing → PostgreSQL (crypto_prices) → Streamlit dashboard  
                                          ↓  
                                      Charts (PNG)

Airflow orchestrates the pipeline (DAG is in `pipeline_dag.py`) and is optional for local exploration.

----

## Quick start (recommended for portfolio / local dev)

Prerequisites:
- Docker & Docker Compose installed (recommended: Docker Desktop)  
- At least 4–8 GB free memory for the services (Postgres + Airflow + Streamlit; Spark increases memory requirements)

1. Copy the environment file

```bash
cp crypto-dashboard-fixed/.env.example .env
# Edit .env and set DB_PASSWORD and other values as needed
```

2. (Optional) If you prefer to run only the Streamlit app without Docker Compose, see the "Local development" section.

3. Run Docker Compose from the repository root (this repo contains the `docker-compose.yml` in the root, which mounts the project into containers):

```bash
docker-compose up --build
```

Notes:
- The compose file brings up a Postgres DB (container name `crypto_db`) and a Streamlit app accessible on http://localhost:8501 by default.  
- If Airflow services are used, they may take extra time to initialize (Airflow DB upgrade and creating the admin user is performed in the webserver command). Airflow UI is available at http://localhost:8081 by default (webserver container maps 8081 -> 8080).

----

## Environment variables (.env)

Use `crypto-dashboard-fixed/.env.example` as a starting point. Important variables to set:

- DB_HOST (default `crypto_db` when using docker-compose)  
- DB_PORT (default `5432` inside the compose network)  
- DB_NAME (default `crypto`)  
- DB_USER  
- DB_PASSWORD (set a secure password)

Airflow security:
- `AIRFLOW__CORE__FERNET_KEY` should be set to a secure, random 32-byte base64 string for production. For local demo, the placeholder is acceptable.

----

## Service endpoints (default ports)

- Streamlit Dashboard: http://localhost:8501  
- pgAdmin (database admin UI): http://localhost:8080 (email/password taken from .env)  
- Airflow Web UI (webserver): http://localhost:8081 (if docker-compose uses Dockerfile.airflow to build webserver)

----

## Running the pipeline manually

Inside the app container or locally with a Python virtualenv you can run:

```bash
python crypto_pipeline.py
```

This will:
- Fetch latest data from CoinGecko  
- Process with Spark (records are filtered and converted)  
- Insert rows into the `crypto_prices` Postgres table  
- Produce `crypto_dashboard.png` with charts

On failure, check the console logs and Postgres connection settings.

----

## Airflow DAG notes

- The Airflow DAG file `pipeline_dag.py` creates a DAG with dag_id `crypto_pipeline_every_15min`.  
- The DAG imports `SimpleCryptoPipeline` from the project path. When running inside the Airflow container created by `docker-compose.yml`, the repository is mounted at `/opt/project`, which matches the DAG's `PROJECT_PATH` logic.  
- If the DAG fails to import, verify that the repository files are present in the Airflow container at `/opt/project` and that Python path logic in the DAG matches the mount.

----

## Database schema (init.sql)

`init.sql` (mounted into Postgres container at init time) contains the table definition used by the project:

```sql
CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    coin_name VARCHAR(50),
    price DECIMAL(15,2),
    market_cap BIGINT,
    volume BIGINT,
    change_24h DECIMAL(10,4),
    timestamp TIMESTAMP DEFAULT NOW(),
    fetched_at TIMESTAMP DEFAULT NOW(),
    price_timestamp TIMESTAMP
);
```

Indexes are added in the SQL script for faster queries by coin and timestamp.

----

## Local development (without Docker)

1. Create and activate a virtualenv

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies for the app

```bash
pip install -r crypto-dashboard-fixed/requirements-app.txt
```

3. Create a local Postgres instance (or point DB_HOST to a running Postgres). Initialize the schema:

```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f init.sql
```

4. Run Streamlit

```bash
streamlit run app.py
```

Notes on PySpark: `pyspark` is required by the pipeline. Installing and running PySpark locally requires a local JVM and enough memory. For small demos with only 5 coins, you can replace Spark processing with pandas by modifying `crypto_pipeline.py`.

----

## Troubleshooting

- Postgres connection errors:
  - Verify `.env` values match the DB container's env (DB_HOST should be `crypto_db` when using Docker Compose)  
  - Check Postgres logs (`docker logs crypto_db`) for startup or permission issues

- Airflow import errors:
  - Confirm the project is mounted into the Airflow container at `/opt/project` (see `docker-compose.yml` volumes for the webserver and scheduler)  
  - Confirm `requirements-airflow.txt` installed needed runtime packages in the Airflow image

- PySpark errors or long build times:
  - Installing `pyspark` via pip downloads Spark and is heavy; builds may take a long time. For a portfolio demo, consider removing `pyspark` and using pandas, or build images ahead of time.

----

## Project structure (important files)

```text
crypto-dashboard-fixed/
├── .env.example
├── .gitignore
├── Dockerfile             # App image (uses requirements-app.txt)
├── Dockerfile.airflow     # Airflow image tweaks (uses requirements-airflow.txt)
├── LICENSE
├── README.md              # <- you are reading this
├── requirements-app.txt
├── requirements-airflow.txt
├── app.py
├── crypto_pipeline.py
└── pipeline_dag.py
```

----

## Notes for portfolio reviewers

- This repository is structured for demonstration. In a production environment you would:
  - Use a dedicated Spark cluster or managed service (Dataproc/EMR)  
  - Avoid installing Spark via pip inside web or airflow images — use pre-baked images or external services  
  - Move secrets to a vault or secret manager instead of a `.env` file  
  - Harden Airflow with a secure Fernet key and credentials

----

## Contributing

If you want improvements, please open an issue or a PR. Suggested small improvements for this portfolio copy:
- Add a lightweight unit test suite for the pipeline (mocking CoinGecko responses)  
- Replace Spark with pandas for tiny datasets to speed up builds for demos  
- Add GitHub Actions that run linting and a smoke test

----

## License

This folder is licensed under the MIT License. See `LICENSE`.
