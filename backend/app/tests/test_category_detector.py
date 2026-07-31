import pandas as pd

from app.services.insight.detectors.category_detector import (
    CategoryDetector,
)
from app.services.insight.insight_models import (
    InsightSeverity,
)


def test_detects_dominant_category() -> None:
    df = pd.DataFrame(
        {
            "status": (
                ["Active"] * 80
                + ["Warning"] * 20
            ),
        }
    )

    detector = CategoryDetector()

    result = detector.detect(df)

    dominant_insights = [
        insight
        for insight in result
        if insight.id
        == "category_dominant_status"
    ]

    assert len(dominant_insights) == 1

    insight = dominant_insights[0]

    assert insight.value == 80.0
    assert insight.severity == (
        InsightSeverity.HIGH
    )


def test_detects_rare_categories() -> None:
    df = pd.DataFrame(
        {
            "status": (
                ["Active"] * 90
                + ["Warning"] * 7
                + ["Suspended"] * 2
                + ["Expelled"]
            ),
        }
    )

    detector = CategoryDetector()

    result = detector.detect(df)

    rare_insights = [
        insight
        for insight in result
        if insight.id
        == "category_rare_status"
    ]

    assert len(rare_insights) == 1

    insight = rare_insights[0]

    rare_categories = (
        insight.metadata[
            "rare_categories"
        ]
    )

    assert "Suspended" in rare_categories
    assert "Expelled" in rare_categories


def test_ignores_identifier_columns() -> None:
    df = pd.DataFrame(
        {
            "student_id": [
                f"SV{i:03d}"
                for i in range(1, 101)
            ],
        }
    )

    detector = CategoryDetector()

    result = detector.detect(df)

    assert result == []


def test_returns_empty_for_empty_dataframe() -> None:
    detector = CategoryDetector()

    result = detector.detect(
        pd.DataFrame()
    )

    assert result == []