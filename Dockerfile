FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
COPY data/raw/ ./data/raw/

CMD ["python", "src/load/load_products.py"]