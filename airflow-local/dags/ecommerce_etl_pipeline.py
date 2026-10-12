import os
from datetime import timedelta

import pendulum
import psycopg

from airflow.sdk import dag, task
from airflow.providers.standard.operators.bash import BashOperator


@dag(
    dag_id="ecommerce_etl_pipeline",
    description="E-commerce ETL with data quality validation",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(
        2026, 10, 1, tz="Asia/Almaty"
    ),
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["ecommerce", "etl"],
)
def ecommerce_etl_pipeline():

    run_etl = BashOperator(
        task_id="run_python_etl",
        bash_command=(
            "python /opt/ecommerce-project/src/load/load_products.py"
        ),
        cwd="/opt/ecommerce-project",
    )

    @task
    def check_data_quality():
        """Validate the transformed products in PostgreSQL."""

        with psycopg.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        ) as connection:

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) AS total_rows,
                        COUNT(*) FILTER (
                            WHERE product_name IS NULL
                               OR TRIM(product_name) = ''
                               OR stock_value <>
                                  ROUND(price * stock_quantity, 2)
                               OR (
                                   stock_quantity = 0
                                   AND stock_status <> 'out_of_stock'
                               )
                               OR (
                                   stock_quantity BETWEEN 1 AND 9
                                   AND stock_status <> 'low_stock'
                               )
                               OR (
                                   stock_quantity >= 10
                                   AND stock_status <> 'in_stock'
                               )
                        ) AS invalid_rows
                    FROM analytics_products;
                """)

                total_rows, invalid_rows = cursor.fetchone()

        print(f"DATA QUALITY: {total_rows} rows checked")
        print(f"DATA QUALITY: {invalid_rows} invalid rows")

        if total_rows == 0:
            raise ValueError("Analytics table is empty")

        if invalid_rows > 0:
            raise ValueError(
                f"Data quality check failed: {invalid_rows} invalid rows"
            )

        print("DATA QUALITY: all checks passed")

    run_etl >> check_data_quality()


ecommerce_etl_pipeline()