# DAG definition for the ecommerce ETL learning pipeline
from datetime import timedelta

import pendulum
from airflow.sdk import dag, task


@dag(
    dag_id="ecommerce_etl_learning",
    description="First Data Engineering learning pipeline",
    schedule=None,
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Almaty"),
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    tags=["learning", "ecommerce"],
)
def ecommerce_etl_learning():

    @task
    def extract():
        """Extract sample products."""
        products = [
            {
                "product_name": "Wireless Mouse",
                "price": 12900,
                "stock_quantity": 30,
            },
            {
                "product_name": "USB-C Hub",
                "price": 24900,
                "stock_quantity": 15,
            },
            {
                "product_name": "Gaming Monitor",
                "price": 189000,
                "stock_quantity": 8,
            },
            {
                "product_name": "Laptop Stand",
                "price": 17900,
                "stock_quantity": 25,
            },
        ]

        print(f"EXTRACT: read {len(products)} products")
        return products

    @task
    def transform(products):
        """Calculate stock value and stock status."""
        transformed = []

        for product in products:
            quantity = product["stock_quantity"]

            if quantity == 0:
                status = "out_of_stock"
            elif quantity < 10:
                status = "low_stock"
            else:
                status = "in_stock"

            transformed.append({
                **product,
                "stock_value": product["price"] * quantity,
                "stock_status": status,
            })

        print(f"TRANSFORM: processed {len(transformed)} products")
        return transformed

    @task
    def load(products):
        """Display the transformed records."""
        for product in products:
            print(
                f"{product['product_name']} | "
                f"stock_value={product['stock_value']} | "
                f"status={product['stock_status']}"
            )

        print(f"LOAD: processed {len(products)} products")
        print("Demo pipeline finished successfully")

    extracted = extract()
    transformed = transform(extracted)
    load(transformed)


ecommerce_etl_learning()