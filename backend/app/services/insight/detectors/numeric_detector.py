import pandas as pd

from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)


class NumericDetector:
    """
    Phát hiện các pattern và bất thường
    trong các cột dữ liệu số.

    Hiện tại detector phát hiện:

    1. Outlier theo phương pháp IQR
    2. Giá trị âm
    3. Mean và median chênh lệch lớn
    """

    OUTLIER_MEDIUM_THRESHOLD = 0.05
    OUTLIER_HIGH_THRESHOLD = 0.15
    OUTLIER_CRITICAL_THRESHOLD = 0.30

    SKEW_RATIO_THRESHOLD = 0.30

    def detect(
        self,
        df: pd.DataFrame,
        data_context: dict | None = None,
    ) -> list[InsightObject]:
        """
        Phân tích tất cả cột numeric trong DataFrame.
        """

        if df.empty:
            return []

        numeric_columns = list(
            df.select_dtypes(
                include="number"
            ).columns
        )

        if not numeric_columns:
            return []

        insights: list[InsightObject] = []

        for column in numeric_columns:
            series = df[column].dropna()

            if series.empty:
                continue

            insights.extend(
                self._detect_outliers(
                    column=column,
                    series=series,
                )
            )

            insights.extend(
                self._detect_negative_values(
                    column=column,
                    series=series,
                    data_context=data_context,
                )
            )

            insights.extend(
                self._detect_mean_median_gap(
                    column=column,
                    series=series,
                )
            )

        return insights

    def _detect_outliers(
        self,
        column: str,
        series: pd.Series,
    ) -> list[InsightObject]:
        """
        Phát hiện outlier bằng phương pháp IQR.
        """

        if len(series) < 4:
            return []

        q1 = float(
            series.quantile(0.25)
        )

        q3 = float(
            series.quantile(0.75)
        )

        iqr = q3 - q1

        if iqr == 0:
            return []

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (
            (series < lower_bound)
            | (series > upper_bound)
        )

        outlier_count = int(
            outlier_mask.sum()
        )

        if outlier_count == 0:
            return []

        total_values = len(series)

        outlier_rate = (
            outlier_count / total_values
        )

        outlier_percent = round(
            outlier_rate * 100,
            2,
        )

        severity = self._get_outlier_severity(
            outlier_rate
        )

        insight = InsightObject(
            id=f"numeric_outlier_{column}",
            type=InsightType.WARNING,
            category="numeric_analysis",
            title=(
                f"Cột {column} có giá trị ngoại lệ"
            ),
            description=(
                f"Phát hiện {outlier_count} giá trị ngoại lệ "
                f"trong cột {column}, chiếm "
                f"{outlier_percent}% số giá trị hợp lệ."
            ),
            metric="outlier_rate",
            value=outlier_percent,
            unit="%",
            threshold=(
                f"Ngoài khoảng "
                f"[{round(lower_bound, 2)}, "
                f"{round(upper_bound, 2)}]"
            ),
            severity=severity,
            evidence=InsightEvidence(
                affected_rows=outlier_count,
                total_rows=total_values,
                calculation=(
                    f"IQR = {round(q3, 2)} - "
                    f"{round(q1, 2)} = "
                    f"{round(iqr, 2)}"
                ),
            ),
            metadata={
                "column": column,
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "iqr": round(iqr, 4),
                "lower_bound": round(
                    lower_bound,
                    4,
                ),
                "upper_bound": round(
                    upper_bound,
                    4,
                ),
                "outlier_count": outlier_count,
                "detector": "NumericDetector",
            },
        )

        return [insight]

    def _detect_negative_values(
        self,
        column: str,
        series: pd.Series,
        data_context: dict | None = None,
    ) -> list[InsightObject]:
        """
        Phát hiện giá trị âm.

        Hiện tại chỉ cảnh báo.
        Sau này có thể dùng semantic context để xác định
        cột nào không được phép âm.
        """

        negative_mask = series < 0

        negative_count = int(
            negative_mask.sum()
        )

        if negative_count == 0:
            return []

        total_values = len(series)

        negative_rate = (
            negative_count / total_values
        )

        negative_percent = round(
            negative_rate * 100,
            2,
        )

        severity = (
            InsightSeverity.HIGH
            if negative_rate >= 0.10
            else InsightSeverity.MEDIUM
        )

        insight = InsightObject(
            id=f"numeric_negative_{column}",
            type=InsightType.WARNING,
            category="data_quality",
            title=(
                f"Cột {column} có giá trị âm"
            ),
            description=(
                f"Phát hiện {negative_count} giá trị âm "
                f"trong cột {column}, chiếm "
                f"{negative_percent}% số giá trị hợp lệ."
            ),
            metric="negative_rate",
            value=negative_percent,
            unit="%",
            threshold="< 0",
            severity=severity,
            evidence=InsightEvidence(
                affected_rows=negative_count,
                total_rows=total_values,
                calculation=(
                    f"{negative_count} / "
                    f"{total_values} * 100 "
                    f"= {negative_percent}%"
                ),
            ),
            metadata={
                "column": column,
                "minimum_value": float(
                    series.min()
                ),
                "negative_count": negative_count,
                "data_context_available": (
                    data_context is not None
                ),
                "detector": "NumericDetector",
            },
        )

        return [insight]

    def _detect_mean_median_gap(
        self,
        column: str,
        series: pd.Series,
    ) -> list[InsightObject]:
        """
        Phát hiện phân phối lệch bằng cách so sánh
        mean và median.
        """

        if len(series) < 4:
            return []

        mean_value = float(
            series.mean()
        )

        median_value = float(
            series.median()
        )

        comparison_base = max(
            abs(median_value),
            1.0,
        )

        gap_ratio = (
            abs(mean_value - median_value)
            / comparison_base
        )

        if gap_ratio < self.SKEW_RATIO_THRESHOLD:
            return []

        gap_percent = round(
            gap_ratio * 100,
            2,
        )

        severity = (
            InsightSeverity.HIGH
            if gap_ratio >= 1.0
            else InsightSeverity.MEDIUM
        )

        insight = InsightObject(
            id=f"numeric_skew_{column}",
            type=InsightType.WARNING,
            category="numeric_analysis",
            title=(
                f"Phân phối cột {column} có dấu hiệu lệch"
            ),
            description=(
                f"Giá trị trung bình của cột {column} là "
                f"{round(mean_value, 2)}, trong khi trung vị "
                f"là {round(median_value, 2)}. "
                f"Mức chênh lệch tương đối là "
                f"{gap_percent}%."
            ),
            metric="mean_median_gap",
            value=gap_percent,
            unit="%",
            threshold=(
                f">= "
                f"{self.SKEW_RATIO_THRESHOLD * 100}%"
            ),
            severity=severity,
            evidence=InsightEvidence(
                affected_rows=len(series),
                total_rows=len(series),
                calculation=(
                    f"|{round(mean_value, 2)} - "
                    f"{round(median_value, 2)}| / "
                    f"{round(comparison_base, 2)} "
                    f"* 100 = {gap_percent}%"
                ),
            ),
            metadata={
                "column": column,
                "mean": round(
                    mean_value,
                    4,
                ),
                "median": round(
                    median_value,
                    4,
                ),
                "gap_ratio": round(
                    gap_ratio,
                    4,
                ),
                "detector": "NumericDetector",
            },
        )

        return [insight]

    def _get_outlier_severity(
        self,
        outlier_rate: float,
    ) -> InsightSeverity:
        """
        Xác định severity dựa trên tỷ lệ outlier.
        """

        if (
            outlier_rate
            >= self.OUTLIER_CRITICAL_THRESHOLD
        ):
            return InsightSeverity.CRITICAL

        if (
            outlier_rate
            >= self.OUTLIER_HIGH_THRESHOLD
        ):
            return InsightSeverity.HIGH

        if (
            outlier_rate
            >= self.OUTLIER_MEDIUM_THRESHOLD
        ):
            return InsightSeverity.MEDIUM

        return InsightSeverity.LOW