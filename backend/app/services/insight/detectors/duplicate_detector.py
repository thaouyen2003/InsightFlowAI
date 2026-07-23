import pandas as pd

from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)


class DuplicateDetector:
    """
    Phát hiện các dòng dữ liệu bị trùng lặp.
    """

    LOW_THRESHOLD = 0.01
    MEDIUM_THRESHOLD = 0.05
    HIGH_THRESHOLD = 0.15

    def detect(
        self,
        df: pd.DataFrame,
    ) -> list[InsightObject]:

        if df.empty:
            return []

        total_rows = len(df)

        duplicate_count = int(
            df.duplicated().sum()
        )

        if duplicate_count == 0:
            return []

        duplicate_rate = (
            duplicate_count / total_rows
        )

        duplicate_percent = round(
            duplicate_rate * 100,
            2,
        )

        severity = self._get_severity(
            duplicate_rate
        )

        insight_type = (
            InsightType.CRITICAL
            if severity == InsightSeverity.CRITICAL
            else InsightType.WARNING
        )

        insight = InsightObject(
            id="duplicate_rows",
            type=insight_type,
            category="data_quality",
            title="Dataset có các dòng dữ liệu trùng lặp",
            description=(
                f"Phát hiện {duplicate_count} dòng trùng lặp "
                f"trên tổng số {total_rows} dòng, "
                f"chiếm {duplicate_percent}% dữ liệu."
            ),
            metric="duplicate_rate",
            value=duplicate_percent,
            unit="%",
            threshold=self._get_threshold_text(
                severity
            ),
            severity=severity,
            evidence=InsightEvidence(
                affected_rows=duplicate_count,
                total_rows=total_rows,
                calculation=(
                    f"{duplicate_count} / {total_rows} * 100 "
                    f"= {duplicate_percent}%"
                ),
            ),
            metadata={
                "duplicate_count": duplicate_count,
                "duplicate_rate": round(
                    duplicate_rate,
                    4,
                ),
                "detector": "DuplicateDetector",
            },
        )

        return [insight]

    def _get_severity(
        self,
        duplicate_rate: float,
    ) -> InsightSeverity:

        if duplicate_rate >= self.HIGH_THRESHOLD:
            return InsightSeverity.CRITICAL

        if duplicate_rate >= self.MEDIUM_THRESHOLD:
            return InsightSeverity.HIGH

        if duplicate_rate >= self.LOW_THRESHOLD:
            return InsightSeverity.MEDIUM

        return InsightSeverity.LOW

    def _get_threshold_text(
        self,
        severity: InsightSeverity,
    ) -> str:

        thresholds = {
            InsightSeverity.LOW: "< 1%",
            InsightSeverity.MEDIUM: "1% - 4.99%",
            InsightSeverity.HIGH: "5% - 14.99%",
            InsightSeverity.CRITICAL: ">= 15%",
        }

        return thresholds[severity]