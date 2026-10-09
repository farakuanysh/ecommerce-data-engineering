import os

import psycopg
from dotenv import load_dotenv


def main():
    load_dotenv()

    connection = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        result = cursor.fetchone()

    print(result[0])

    connection.close()


if __name__ == "__main__":
    main()