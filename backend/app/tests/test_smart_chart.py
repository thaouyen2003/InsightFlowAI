import pandas as pd

from app.services.dashboard.chart_generator import (
    ChartGenerator,
)
from app.services.dashboard.data_context_builder import (
    DataContextBuilder,
)
from app.services.dashboard.dataset_classifier import (
    DatasetClassifier,
)


def test_smart_chart_generation():
    df = pd.DataFrame({
        "order_id": [
            "O001",
            "O002",
            "O003",
            "O004",
        ],
        "order_date": [
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
            "2026-04-01",
        ],
        "category": [
            "Laptop",
            "Phone",
            "Laptop",
            "Tablet",
        ],
        "region": [
            "North",
            "South",
            "North",
            "Central",
        ],
        "quantity": [
            1,
            2,
            3,
            1,
        ],
        "revenue": [
            1200,
            800,
            1000,
            700,
        ],
    })

    context = DataContextBuilder().build(df)

    dataset_profile = (
        DatasetClassifier().classify(
            context
        )
    )

    charts = ChartGenerator().generate(
        df=df,
        data_context=context,
        dataset_profile=dataset_profile,
    )

    chart_types = {
        chart["type"]
        for chart in charts
    }

    assert "line" in chart_types
    assert "bar" in chart_types
    assert len(charts) <= 5

    for chart in charts:
        assert "id" in chart
        assert "title" in chart
        assert "score" in chart
        assert "reason" in chart
        assert "data" in chart