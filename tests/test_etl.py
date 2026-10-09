from decimal import Decimal

import pytest

from src.load import load_products


def test_extract_data_reads_all_products():
    """Check that all products are extracted correctly."""

    rows = load_products.extract_data()

    assert len(rows) == 4
    assert rows[0][0] == "Wireless Mouse"
    assert rows[0][1] == "Accessories"
    assert rows[0][2] == Decimal("12900")
    assert rows[0][3] == 30


def test_extract_data_rejects_negative_price(tmp_path, monkeypatch):
    """Check that products with negative prices are rejected."""

    csv_file = tmp_path / "products.csv"

    csv_file.write_text(
        "product_name,category,price,stock_quantity\n"
        "Bad Product,Accessories,-100,5\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(load_products, "CSV_PATH", csv_file)

    with pytest.raises(ValueError, match="Negative price or quantity"):
        load_products.extract_data()