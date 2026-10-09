import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def fetch_one(query):
    """Execute a query and return its first result row."""
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()


def test_staging_and_analytics_counts_match():
    """All staged products should reach the analytics table."""
    staging_count, analytics_count = fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM stg_products),
            (SELECT COUNT(*) FROM analytics_products);
    """)

    assert staging_count > 0
    assert analytics_count == staging_count


def test_stock_value_is_calculated_correctly():
    """Stock value must equal price multiplied by stock quantity."""
    invalid_count = fetch_one("""
        SELECT COUNT(*)
        FROM analytics_products
        WHERE stock_value <> ROUND(price * stock_quantity, 2);
    """)[0]

    assert invalid_count == 0


def test_stock_status_is_correct():
    """Stock status must match the quantity rules."""
    invalid_count = fetch_one("""
        SELECT COUNT(*)
        FROM analytics_products
        WHERE
            (stock_quantity = 0
                AND stock_status <> 'out_of_stock')
            OR
            (stock_quantity BETWEEN 1 AND 9
                AND stock_status <> 'low_stock')
            OR
            (stock_quantity >= 10
                AND stock_status <> 'in_stock');
    """)[0]

    assert invalid_count == 0


def test_product_names_are_not_empty():
    """Every analytics product must have a non-empty name."""
    invalid_count = fetch_one("""
        SELECT COUNT(*)
        FROM analytics_products
        WHERE product_name IS NULL
           OR TRIM(product_name) = '';
    """)[0]

    assert invalid_count == 0