import pandas as pd

from app.services.dashboard.data_context_builder import (
    DataContextBuilder,
)
from app.services.dashboard.dataset_classifier import (
    DatasetClassifier,
)
from app.services.dashboard.kpi_generator import (
    KPIGenerator,
)


def test_sales_smart_kpis():
    df = pd.DataFrame({
        "order_id": [
            "O001",
            "O002",
            "O003",
        ],
        "customer_id": [
            "C001",
            "C002",
            "C001",
        ],
        "order_date": [
            "2026-07-01",
            "2026-07-02",
            "2026-07-03",
        ],
        "product_category": [
            "Laptop",
            "Phone",
            "Laptop",
        ],
        "quantity": [
            1,
            2,
            3,
        ],
        "revenue": [
            1200,
            800,
            1000,
        ],
        "profit": [
            200,
            100,
            150,
        ],
    })

    context = DataContextBuilder().build(df)

    dataset_profile = (
        DatasetClassifier().classify(
            context
        )
    )

    kpis = KPIGenerator().generate(
        df=df,
        data_context=context,
        dataset_profile=dataset_profile,
    )

    kpi_ids = {
        kpi["id"]
        for kpi in kpis
    }

    assert "total_revenue" in kpi_ids
    assert "total_profit" in kpi_ids
    assert "total_orders" in kpi_ids
    assert "unique_customers" in kpi_ids

    total_revenue = next(
        kpi
        for kpi in kpis
        if kpi["id"] == "total_revenue"
    )

    assert total_revenue["value"] == 3000

    total_orders = next(
        kpi
        for kpi in kpis
        if kpi["id"] == "total_orders"
    )

    assert total_orders["value"] == 3


def test_identifier_not_summed():
    df = pd.DataFrame({
        "customer_id": [
            1001,
            1002,
            1003,
        ],
        "customer_state": [
            "SP",
            "RJ",
            "SP",
        ],
    })

    context = DataContextBuilder().build(df)

    dataset_profile = (
        DatasetClassifier().classify(
            context
        )
    )

    kpis = KPIGenerator().generate(
        df=df,
        data_context=context,
        dataset_profile=dataset_profile,
    )

    titles = {
        kpi["title"]
        for kpi in kpis
    }

    assert "Total Customer Id" not in titles