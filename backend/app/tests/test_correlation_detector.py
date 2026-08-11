import pandas as pd

from app.services.insight.detectors.correlation_detector import (
    CorrelationDetector,
)


def test_detect_positive_correlation() -> None:
    df = pd.DataFrame(
        {
            "student_id": [
                1,
                2,
                3,
                4,
                5,
            ],
            "attendance": [
                60,
                70,
                80,
                90,
                100,
            ],
            "gpa": [
                5.5,
                6.2,
                7.1,
                8.3,
                9.2,
            ],
        }
    )

    detector = CorrelationDetector()

    results = detector.detect(df)

    assert len(results) >= 1

    result = results[0]

    assert result["knowledge_type"] == "correlation"
    assert result["direction"] == "positive"
    assert result["strength"] == "very_strong"

    assert "attendance" in result["columns"]
    assert "gpa" in result["columns"]

    assert result["correlation_coefficient"] > 0.8


def test_detect_negative_correlation() -> None:
    df = pd.DataFrame(
        {
            "absence_days": [
                1,
                2,
                3,
                4,
                5,
            ],
            "gpa": [
                9.0,
                8.2,
                7.3,
                6.4,
                5.5,
            ],
        }
    )

    detector = CorrelationDetector()

    results = detector.detect(df)

    assert len(results) >= 1

    result = results[0]

    assert result["direction"] == "negative"
    assert result["correlation_coefficient"] < -0.8


def test_ignore_id_column() -> None:
    df = pd.DataFrame(
        {
            "student_id": [
                100,
                200,
                300,
                400,
                500,
            ],
            "attendance": [
                60,
                70,
                80,
                90,
                100,
            ],
            "gpa": [
                5.5,
                6.2,
                7.1,
                8.3,
                9.2,
            ],
        }
    )

    detector = CorrelationDetector()

    results = detector.detect(df)

    for result in results:
        assert "student_id" not in result["columns"]


def test_return_empty_when_not_enough_numeric_columns() -> None:
    df = pd.DataFrame(
        {
            "student_name": [
                "An",
                "Bình",
                "Chi",
            ],
            "gpa": [
                7.0,
                8.0,
                9.0,
            ],
        }
    )

    detector = CorrelationDetector()

    results = detector.detect(df)

    assert results == []


def test_ignore_weak_correlation() -> None:
    df = pd.DataFrame(
        {
            "column_a": [
                1,
                2,
                3,
                4,
                5,
                6,
            ],
            "column_b": [
                10,
                2,
                8,
                4,
                7,
                5,
            ],
        }
    )

    detector = CorrelationDetector()

    results = detector.detect(df)

    assert results == []