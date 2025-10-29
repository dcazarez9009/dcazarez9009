# crypto-dashboard-fixed

This folder contains a cleaned-up, portfolio-ready copy of the crypto-dashboard project.
It includes small fixes to make local development and Docker builds more predictable.

## What changed

- Added `.gitignore` and `.env.example`
- Split `requirements.txt` into `requirements-app.txt` (for the Streamlit app) and `requirements-airflow.txt` (for Airflow DAG runtime deps)
- Updated `Dockerfile` and `Dockerfile.airflow` to install the corresponding requirements files
- Added an `MIT` license
- Updated README content and clarified usage of `.env.example`

## Quick start (using the original docker-compose.yml in the repository root)

1. Copy environment variables

```bash
cp crypto-dashboard-fixed/.env.example .env
# Edit .env values if necessary
```

2. Build and run (from repository root)

```bash
docker-compose up --build
```

3. Access services
- Streamlit Dashboard: http://localhost:8501
- pgAdmin: http://localhost:8080
- Airflow Web UI (if using Dockerfile.airflow build): http://localhost:8081
