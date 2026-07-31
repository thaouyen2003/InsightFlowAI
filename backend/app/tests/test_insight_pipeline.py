from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)
from app.services.insight.insight_pipeline import (
    InsightPipeline,
)


def create_insight(
    insight_id: str,
    severity: InsightSeverity,
    value: float,
) -> InsightObject:
    return InsightObject(
        id=insight_id,
        type=InsightType.WARNING,
        category="data_quality",
        title=f"Insight {insight_id}",
        description="Insight dùng để test pipeline.",
        metric="test_metric",
        value=value,
        unit="%",
        threshold="test",
        severity=severity,
        evidence=InsightEvidence(
            affected_rows=1,
            total_rows=10,
            calculation="1 / 10 * 100",
        ),
        metadata={
            "source": "test",
        },
    )


def test_pipeline_removes_duplicate_ids() -> None:
    pipeline = InsightPipeline()

    low_insight = create_insight(
        insight_id="missing_gpa",
        severity=InsightSeverity.LOW,
        value=5,
    )

    high_insight = create_insight(
        insight_id="missing_gpa",
        severity=InsightSeverity.HIGH,
        value=30,
    )

    result = pipeline.process(
        [
            low_insight,
            high_insight,
        ]
    )

    assert len(result) == 1
    assert result[0].severity == (
        InsightSeverity.HIGH
    )


def test_pipeline_sorts_by_severity() -> None:
    pipeline = InsightPipeline()

    low_insight = create_insight(
        insight_id="low",
        severity=InsightSeverity.LOW,
        value=5,
    )

    critical_insight = create_insight(
        insight_id="critical",
        severity=InsightSeverity.CRITICAL,
        value=40,
    )

    result = pipeline.process(
        [
            low_insight,
            critical_insight,
        ]
    )

    assert result[0].severity == (
        InsightSeverity.CRITICAL
    )