from datetime import datetime, timedelta
import sys
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator

# ✅ Ensure project path is accessible
PROJECT_PATH = "/opt/project"
if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)

from crypto_pipeline import SimpleCryptoPipeline

# ✅ Setup logging
logger = logging.getLogger(__name__)

def run_pipeline():
    """Run the crypto pipeline with detailed logging"""
    try:
        logger.info("🚀 Starting pipeline execution")
        
        pipeline = SimpleCryptoPipeline()
        logger.info("✅ Pipeline initialized")
        
        # Run the full ETL pipeline
        success = pipeline.run_full_pipeline()
        
        if success:
            logger.info("✅ Pipeline completed successfully")
            return True
        else:
            logger.error("❌ Pipeline returned False - check logs above")
            raise Exception("Pipeline execution returned False")
            
    except Exception as e:
        logger.error(f"❌ Pipeline failed with error: {str(e)}", exc_info=True)
        raise  # Let Airflow handle retry logic

# ✅ Default arguments for Airflow task behavior
default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=15),  # Max time before task fails
    "email_on_failure": False,
    "email_on_retry": False,
}

# ✅ DAG definition
with DAG(
    dag_id="crypto_pipeline_every_15min",
    default_args=default_args,
    description="Run crypto ETL pipeline every 15 minutes",
    schedule_interval="*/15 * * * *",  # ✅ Correct key for scheduling
    start_date=datetime(2024, 1, 1, 0, 0),  # clean start time (midnight)
    catchup=False,  # ✅ Prevents backfilling missed runs
    max_active_runs=1,  # ✅ Prevent overlapping runs
    tags=["crypto", "etl", "production"],
) as dag:

    run_etl = PythonOperator(
        task_id="run_crypto_pipeline",
        python_callable=run_pipeline,
        pool="default_pool",
        pool_slots=1,  # ✅ Prevents concurrency issues
    )

    run_etl

