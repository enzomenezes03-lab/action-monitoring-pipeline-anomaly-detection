import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

DIR = os.path.dirname(__file__)
SRC_PATH = os.path.join(DIR, "..", "src")
sys.path.append(SRC_PATH)

from extract_brapi import main as main_brapi
from extract_yfinance import main as main_yfinance
from modeling_gold import main as main_gold

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stocks_pipeline",
    schedule="0 21 * * *",
    start_date=datetime(2026, 7, 13),
    catchup=False,
    default_args=default_args,
) as dag:

    task1 = PythonOperator(
        task_id="extract_yfinance",
        python_callable=main_yfinance,
    )

    task2 = PythonOperator(
        task_id="extract_brapi",
        python_callable=main_brapi,
    )

    task3 = BashOperator(
        task_id="transform_silver",
        bash_command="docker exec action-monitoring-pipeline-anomaly-detection-spark-1 /opt/spark/bin/spark-submit --jars /opt/spark_jars/postgresql-42.7.3.jar /opt/spark_apps/transform_silver.py",
    )

    task4 = PythonOperator(
        task_id="model_gold",
        python_callable=main_gold,
    )

    [task1, task2] >> task3 >> task4