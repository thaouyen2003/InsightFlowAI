from app.services.dashboard.dashboard_composer import (
    DashboardComposer,
)


def test_dashboard_composer():
    kpis = [
        {
            "id": "total_revenue",
            "title": "Total Revenue",
            "value": 5000,
            "column": "revenue",
            "aggregation": "sum",
            "priority": 100,
        },
        {
            "id": "total_orders",
            "title": "Total Orders",
            "value": 10,
            "column": "order_id",
            "aggregation": "nunique",
            "priority": 90,
        },
        {
            "id": "total_sales_channel",
            "title": "Total Sales Channel",
            "value": 0,
            "column": "sales_channel",
            "aggregation": "sum",
            "priority": 30,
        },
    ]

    charts = [
        {
            "id": "line_order_date_revenue",
            "type": "line",
            "title": "Revenue Trend",
            "x_axis": "order_date",
            "y_axis": "revenue",
            "score": 100,
            "data": [
                {
                    "x": "2026-01-01",
                    "y": 1000,
                }
            ],
        },
        {
            "id": "bar_category_revenue",
            "type": "bar",
            "title": "Revenue by Category",
            "dimension": "category",
            "measure": "revenue",
            "score": 90,
            "data": [
                {
                    "label": "Laptop",
                    "value": 3000,
                }
            ],
        },
        {
            "id": "pie_category_revenue",
            "type": "pie",
            "title": (
                "Revenue Distribution "
                "by Category"
            ),
            "dimension": "category",
            "measure": "revenue",
            "score": 80,
            "data": [
                {
                    "name": "Laptop",
                    "value": 3000,
                }
            ],
        },
    ]

    composer = DashboardComposer()

    result = composer.compose(
        kpis=kpis,
        charts=charts,
        data_context={},
        dataset_profile={
            "dataset_type": "sales",
        },
    )

    selected_kpi_ids = {
        kpi["id"]
        for kpi in result["kpis"]
    }

    selected_chart_ids = {
        chart["id"]
        for chart in result["charts"]
    }

    assert "total_revenue" in selected_kpi_ids
    assert "total_orders" in selected_kpi_ids

    assert (
        "total_sales_channel"
        not in selected_kpi_ids
    )

    assert (
        "line_order_date_revenue"
        in selected_chart_ids
    )

    assert (
        "bar_category_revenue"
        in selected_chart_ids
    )

    assert (
        "pie_category_revenue"
        not in selected_chart_ids
    )

    assert (
        result["composition_summary"][
            "selected_kpi_count"
        ]
        == 2
    )

    assert (
        result["layout"]["chart_columns"]
        == 2
    )