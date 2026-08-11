import pandas as pd

from app.services.dashboard.insight_generator import (
    InsightGenerator,
)


def test_insight_generator():
    df = pd.DataFrame({
        "order_date": [
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
        ],
        "category": [
            "Laptop",
            "Phone",
            "Laptop",
        ],
        "revenue": [
            1000,
            1500,
            2000,
        ],
    })

    kpis = [
        {
            "id": "total_revenue",
            "title": "Total Revenue",
            "value": 4500,
            "format": "currency",
            "column": "revenue",
            "aggregation": "sum",
            "priority": 100,
        }
    ]

    charts = [
        {
            "id": "line_order_date_revenue",
            "type": "line",
            "title": "Revenue Trend",
            "x_axis": "order_date",
            "y_axis": "revenue",
            "data": [
                {
                    "x": "2026-01-01",
                    "y": 1000,
                },
                {
                    "x": "2026-02-01",
                    "y": 1500,
                },
                {
                    "x": "2026-03-01",
                    "y": 2000,
                },
            ],
        },
        {
            "id": "bar_category_revenue",
            "type": "bar",
            "title": "Revenue by Category",
            "dimension": "category",
            "measure": "revenue",
            "data": [
                {
                    "label": "Laptop",
                    "value": 3000,
                },
                {
                    "label": "Phone",
                    "value": 1500,
                },
            ],
        },
    ]

    result = InsightGenerator().generate(
        df=df,
        kpis=kpis,
        charts=charts,
        data_context={
            "columns": [],
        },
        dataset_profile={
            "dataset_type": "sales",
            "confidence": 0.9,
        },
        warnings=[],
    )

    insight_types = {
        insight["type"]
        for insight in result["insights"]
    }

    assert "trend" in insight_types
    assert "contribution" in insight_types
    assert "kpi" in insight_types

    trend_insight = next(
        insight
        for insight in result["insights"]
        if insight["type"] == "trend"
    )

    assert (
        trend_insight["severity"]
        == "positive"
    )

    assert (
        trend_insight["evidence"][
            "percentage_change"
        ]
        == 100
    )

    contribution_insight = next(
        insight
        for insight in result["insights"]
        if insight["type"]
        == "contribution"
    )

    assert (
        contribution_insight[
            "evidence"
        ]["top_category"]
        == "Laptop"
    )

    assert (
        len(result["recommendations"])
        >= 1
    )