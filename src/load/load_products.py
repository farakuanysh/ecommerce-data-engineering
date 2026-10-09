import csv
import logging
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "products.csv"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Logging to console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "etl.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Load database settings
load_dotenv(PROJECT_ROOT / ".env")


def extract_data():
    """Read and validate product data from CSV."""

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    required_columns = {
        "product_name",
        "category",
        "price",
        "stock_quantity",
    }

    rows = []

    with CSV_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        if (
            not reader.fieldnames
            or not required_columns.issubset(reader.fieldnames)
        ):
            raise ValueError(
                f"CSV must contain columns: {sorted(required_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            product_name = (row["product_name"] or "").strip()
            category = (row["category"] or "").strip()

            if not product_name or not category:
                raise ValueError(
                    f"Empty product name or category at line {line_number}"
                )

            try:
                price = Decimal((row["price"] or "").strip())
                stock_quantity = int(
                    (row["stock_quantity"] or "").strip()
                )
            except (InvalidOperation, TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid price or quantity at line {line_number}"
                ) from error

            if not price.is_finite():
                raise ValueError(
                    f"Invalid price at line {line_number}"
                )

            if price < 0 or stock_quantity < 0:
                raise ValueError(
                    f"Negative price or quantity at line {line_number}"
                )

            rows.append(
                (product_name, category, price, stock_quantity)
            )

    if not rows:
        raise ValueError("CSV contains no product rows")

    logger.info("EXTRACT: read %s products from CSV", len(rows))
    return rows


def load_and_transform(rows):
    """Load staging data, transform it, and load analytics data."""

    required_env = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [key for key in required_env if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Missing settings in .env: {', '.join(missing)}"
        )

    # Exiting the connection context commits the transaction
    # if all database operations succeed.
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stg_products (
                    staging_id BIGSERIAL PRIMARY KEY,
                    product_name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    price NUMERIC(12, 2) NOT NULL
                        CHECK (price >= 0),
                    stock_quantity INTEGER NOT NULL
                        CHECK (stock_quantity >= 0),
                    loaded_at TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_products (
                    source_staging_id BIGINT PRIMARY KEY,
                    product_name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    price NUMERIC(12, 2) NOT NULL
                        CHECK (price >= 0),
                    stock_quantity INTEGER NOT NULL
                        CHECK (stock_quantity >= 0),
                    stock_value NUMERIC(14, 2) NOT NULL
                        CHECK (stock_value >= 0),
                    stock_status VARCHAR(20) NOT NULL
                        CHECK (
                            stock_status IN (
                                'out_of_stock',
                                'low_stock',
                                'in_stock'
                            )
                        ),
                    transformed_at TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Full refresh of the staging table.
            cursor.execute(
                "TRUNCATE TABLE stg_products RESTART IDENTITY;"
            )

            cursor.executemany("""
                INSERT INTO stg_products (
                    product_name,
                    category,
                    price,
                    stock_quantity
                )
                VALUES (%s, %s, %s, %s);
            """, rows)

            cursor.execute("SELECT COUNT(*) FROM stg_products;")
            staging_count = cursor.fetchone()[0]

            # Full refresh of the analytics table.
            cursor.execute("TRUNCATE TABLE analytics_products;")

            cursor.execute("""
                INSERT INTO analytics_products (
                    source_staging_id,
                    product_name,
                    category,
                    price,
                    stock_quantity,
                    stock_value,
                    stock_status
                )
                SELECT
                    staging_id,
                    TRIM(product_name),
                    INITCAP(TRIM(category)),
                    price,
                    stock_quantity,
                    ROUND(price * stock_quantity, 2),
                    CASE
                        WHEN stock_quantity = 0
                            THEN 'out_of_stock'
                        WHEN stock_quantity < 10
                            THEN 'low_stock'
                        ELSE 'in_stock'
                    END
                FROM stg_products;
            """)

            cursor.execute(
                "SELECT COUNT(*) FROM analytics_products;"
            )
            analytics_count = cursor.fetchone()[0]

    # These messages are logged after the transaction commits.
    logger.info("LOAD: inserted %s rows into staging", staging_count)
    logger.info(
        "TRANSFORM + LOAD: %s rows written to analytics_products",
        analytics_count,
    )

    return staging_count, analytics_count


def main():
    logger.info("ETL pipeline started")

    try:
        rows = extract_data()
        staging_count, analytics_count = load_and_transform(rows)

        logger.info("ETL PIPELINE FINISHED SUCCESSFULLY")
        logger.info("Staging rows: %s", staging_count)
        logger.info("Analytics rows: %s", analytics_count)

    except Exception:
        logger.exception("ETL pipeline failed")
        raise


if __name__ == "__main__":
    main()