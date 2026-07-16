import pandas as pd

from app.services.dashboard.data_context_builder import (
    DataContextBuilder,
)
from app.services.dashboard.dataset_classifier import (
    DatasetClassifier,
)


def test_sales_dataset_classifier():
    df = pd.DataFrame({
        "order_id": [
            "O001",
            "O002",
            "O003",
        ],
        "order_date": [
            "2026-07-01",
            "2026-07-02",
            "2026-07-03",
        ],
        "customer_id": [
            "C001",
            "C002",
            "C003",
        ],
        "product_name": [
            "Laptop",
            "Phone",
            "Mouse",
        ],
        "quantity": [
            1,
            2,
            3,
        ],
        "revenue": [
            1200000,
            900000,
            300000,
        ],
    })

    context = DataContextBuilder().build(df)

    result = DatasetClassifier().classify(
        context
    )

    assert result["dataset_type"] == "sales"
    assert result["score"] >= 3
    assert result["confidence"] > 0
    assert len(
        result["matched_signals"]
    ) > 0


def test_generic_dataset_classifier():
    df = pd.DataFrame({
        "column_a": [
            "A",
            "B",
            "C",
        ],
        "column_b": [
            "X",
            "Y",
            "Z",
        ],
    })

    context = DataContextBuilder().build(df)

    result = DatasetClassifier().classify(
        context
    )

    assert result["dataset_type"] == "generic"