import re

import pandas as pd

from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)


class MissingDetector:
    """
    Phát hiện các cột có dữ liệu bị thiếu.

    Không gọi LLM.
    Không thay đổi DataFrame.
    Chỉ sinh InsightObject.
    """

    LOW_THRESHOLD = 0.05
    MEDIUM_THRESHOLD = 0.15
    HIGH_THRESHOLD = 0.30

    def detect(
        self,
        df: pd.DataFrame,
    ) -> list[InsightObject]:

        if df.empty:
            return []

        total_rows = len(df)

        if total_rows == 0:
            return []

        insights: list[InsightObject] = []

        for column in df.columns:
            missing_count = int(
                df[column].isna().sum()
            )

            if missing_count == 0:
                continue

            missing_rate = (
                missing_count / total_rows
            )

            missing_percent = round(
                missing_rate * 100,
                2,
            )

            insight = self._build_insight(
                column=str(column),
                missing_count=missing_count,
                total_rows=total_rows,
                missing_percent=missing_percent,
                missing_rate=missing_rate,
            )

            insights.append(insight)

        return sorted(
            insights,
            key=lambda item: float(item.value or 0),
            reverse=True,
        )

    def _build_insight(
        self,
        column: str,
        missing_count: int,
        total_rows: int,
        missing_percent: float,
        missing_rate: float,
    ) -> InsightObject:

        severity = self._get_severity(
            missing_rate
        )

        insight_type = self._get_type(
            severity
        )

        safe_column = self._slugify(column)

        return InsightObject(
            id=f"missing_{safe_column}",
            type=insight_type,
            category="data_quality",
            title=(
                f"Cột {column} có dữ liệu bị thiếu"
            ),
            description=(
                f"Cột {column} có {missing_count} giá trị "
                f"bị thiếu trên tổng số {total_rows} dòng, "
                f"chiếm {missing_percent}% dữ liệu."
            ),
            metric="missing_rate",
            value=missing_percent,
            unit="%",
            threshold=self._get_threshold_text(
                severity
            ),
            severity=severity,
            evidence=InsightEvidence(
                column=column,
                affected_rows=missing_count,
                total_rows=total_rows,
                calculation=(
                    f"{missing_count} / {total_rows} * 100 "
                    f"= {missing_percent}%"
                ),
            ),
            metadata={
                "missing_count": missing_count,
                "missing_rate": round(
                    missing_rate,
                    4,
                ),
                "detector": "MissingDetector",
            },
        )

    def _get_severity(
        self,
        missing_rate: float,
    ) -> InsightSeverity:

        if missing_rate >= self.HIGH_THRESHOLD:
            return InsightSeverity.CRITICAL

        if missing_rate >= self.MEDIUM_THRESHOLD:
            return InsightSeverity.HIGH

        if missing_rate >= self.LOW_THRESHOLD:
            return InsightSeverity.MEDIUM

        return InsightSeverity.LOW

    def _get_type(
        self,
        severity: InsightSeverity,
    ) -> InsightType:

        if severity == InsightSeverity.CRITICAL:
            return InsightType.CRITICAL

        return InsightType.WARNING

    def _get_threshold_text(
        self,
        severity: InsightSeverity,
    ) -> str:

        thresholds = {
            InsightSeverity.LOW: "< 5%",
            InsightSeverity.MEDIUM: "5% - 14.99%",
            InsightSeverity.HIGH: "15% - 29.99%",
            InsightSeverity.CRITICAL: ">= 30%",
        }

        return thresholds[severity]

    def _slugify(
        self,
        value: str,
    ) -> str:

        normalized = value.strip().lower()

        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            normalized,
        )

        return normalized.strip("_")