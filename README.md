\# E-commerce Data Engineering Pipeline



An end-to-end learning project that demonstrates how to extract, validate, transform, and load e-commerce product data using Python, PostgreSQL, Docker, and Apache Airflow.



\## Overview



This project implements a small ETL pipeline that reads product data from a CSV file, validates the input, loads records into PostgreSQL staging tables, transforms the data, and writes the results to an analytics table.



Apache Airflow orchestrates the pipeline, while automated tests validate data quality.



\## Architecture



```text

CSV Source

&#x20;   |

&#x20;   v

Python Extract \& Validation

&#x20;   |

&#x20;   v

PostgreSQL Staging

&#x20;   |

&#x20;   v

SQL Transformations

&#x20;   |

&#x20;   v

Analytics Table

&#x20;   |

&#x20;   v

Data Quality Checks

```



The workflow can be run locally or with Docker. Apache Airflow provides orchestration and task monitoring.



\## Tech Stack



\- \*\*Python\*\* — ETL logic and input validation

\- \*\*PostgreSQL\*\* — relational database and data storage

\- \*\*SQL\*\* — joins, aggregations, transformations, and analytical queries

\- \*\*Psycopg\*\* — Python-to-PostgreSQL connectivity

\- \*\*pytest\*\* — automated testing

\- \*\*Docker and Docker Compose\*\* — reproducible development environment

\- \*\*Apache Airflow\*\* — workflow orchestration and monitoring

\- \*\*Git\*\* — version control



\## Project Structure



```text

ecommerce-project/

├── data/

│   └── raw/

│       └── products.csv

├── sql/

│   └── SQL scripts

├── src/

│   └── load/

│       └── load\_products.py

├── tests/

│   ├── test\_etl.py

│   └── test\_data\_quality.py

├── airflow-local/

│   ├── dags/

│   │   ├── ecommerce\_etl\_learning.py

│   │   └── ecommerce\_etl\_pipeline.py

│   ├── Dockerfile

│   └── docker-compose.yaml

├── Dockerfile

├── docker-compose.yml

├── requirements.txt

├── .dockerignore

├── .gitignore

└── README.md

```



\## Data Pipeline



\### 1. Extract



The ETL script reads products from `data/raw/products.csv` and validates required columns, product names, categories, prices, and stock quantities.



\### 2. Load to Staging



Validated records are loaded into the PostgreSQL staging table `stg\_products`.



\### 3. Transform



SQL transformations calculate:



\- `stock\_value` — product price multiplied by stock quantity

\- `stock\_status` — `out\_of\_stock`, `low\_stock`, or `in\_stock`

\- Normalized product names and categories



\### 4. Load to Analytics



Transformed records are written to `analytics\_products`.



The current implementation performs a full refresh of its staging and analytics tables on each successful pipeline run.



\### 5. Data Quality



Automated tests check input validation, record counts, stock value calculations, stock statuses, and non-empty product names.



\### 6. Orchestration



Apache Airflow runs the ETL task and checks the resulting data. Task status and execution logs can be inspected in the Airflow web interface.



\## Local Setup



\### Prerequisites



\- Python

\- PostgreSQL

\- Git



\### Install dependencies



Create and activate a virtual environment, then install the project dependencies:



```bash

pip install -r requirements.txt

```



Configure database connection variables in a local `.env` file. Do not commit this file.



\### Run the ETL pipeline



```bash

python src/load/load\_products.py

```



\### Run tests



```bash

python -m pytest -v

```



Database quality tests require a running PostgreSQL database with the required tables and data.



\## Docker Setup



Create a local `.env.docker` file with the required PostgreSQL settings. Do not commit credentials.



Start PostgreSQL:



```bash

docker compose --env-file .env.docker up -d db

```



Run the ETL pipeline in a container:



```bash

docker compose --env-file .env.docker run --build --rm etl

```



Connect to the Docker database from the host using `localhost:5434`.



\## Apache Airflow



The Airflow environment is configured separately in `airflow-local/`.



Start from that directory:



```bash

docker compose config -q

docker compose up airflow-init

docker compose build

docker compose up -d

```



Open the Airflow UI at:



http://localhost:8080



The `ecommerce\_etl\_pipeline` DAG runs the Python ETL and performs data quality validation.



These commands describe the initial setup. On an existing installation, do not rerun initialization unnecessarily.



\## Future Improvements



\- Incremental data loading

\- Structured logging and improved error handling

\- More data quality checks

\- Automated test execution in CI

\- dbt models and a data warehouse layer

\- Airflow scheduling and operational monitoring



\## Project Goal



The goal of this project is to develop practical Data Engineering skills through building, testing, containerizing, and orchestrating a complete ETL workflow.



