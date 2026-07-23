import re

import pandas as pd

from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)


class CorrelationDetector:
    """
    Phát hiện mối tương quan tuyến tính giữa các cột số.

    Không gọi LLM.
    Không thay đổi DataFrame.
    Chỉ sinh InsightObject.
    """

    MIN_CORRELATION = 0.40
    STRONG_THRESHOLD = 0.60
    VERY_STRONG_THRESHOLD = 0.80
    MAX_RESULTS = 10

    def detect(
        self,
        df: pd.DataFrame,
    ) -> list[InsightObject]:

        if df.empty:
            return []

        numeric_df = self._prepare_numeric_dataframe(
            df
        )

        if numeric_df.shape[1] < 2:
            return []

        correlation_matrix = numeric_df.corr(
            method="pearson"
        )

        insights: list[InsightObject] = []

        columns = correlation_matrix.columns.tolist()

        for first_index in range(len(columns)):
            for second_index in range(
                first_index + 1,
                len(columns),
            ):
                first_column = columns[first_index]
                second_column = columns[second_index]

                coefficient = correlation_matrix.loc[
                    first_column,
                    second_column,
                ]

                if pd.isna(coefficient):
                    continue

                coefficient = float(coefficient)

                if (
                    abs(coefficient)
                    < self.MIN_CORRELATION
                ):
                    continue

                insight = self._build_insight(
                    first_column=first_column,
                    second_column=second_column,
                    coefficient=coefficient,
                )

                insights.append(insight)

        return sorted(
            insights,
            key=lambda item: abs(
                float(item.value or 0)
            ),
            reverse=True,
        )[: self.MAX_RESULTS]

    def _prepare_numeric_dataframe(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Lấy các cột số hợp lệ để tính tương quan.

        Loại bỏ:
        - Cột ID hoặc mã
        - Cột hoàn toàn rỗng
        - Cột chỉ có một giá trị
        """

        numeric_df = df.select_dtypes(
            include="number",
        ).copy()

        valid_columns: list[str] = []

        for column in numeric_df.columns:
            column_name = str(column)

            if self._is_id_column(column_name):
                continue

            non_null_values = numeric_df[
                column
            ].dropna()

            if non_null_values.empty:
                continue

            if non_null_values.nunique() <= 1:
                continue

            valid_columns.append(column_name)

        return numeric_df[valid_columns]

    def _build_insight(
        self,
        first_column: str,
        second_column: str,
        coefficient: float,
    ) -> InsightObject:

        direction = self._get_direction(
            coefficient
        )

        strength = self._get_strength(
            coefficient
        )

        severity = self._get_severity(
            coefficient
        )

        insight_type = self._get_type(
            coefficient
        )

        rounded_coefficient = round(
            coefficient,
            4,
        )

        display_coefficient = round(
            coefficient,
            2,
        )

        safe_first_column = self._slugify(
            first_column
        )

        safe_second_column = self._slugify(
            second_column
        )

        direction_text = {
            "positive": "dương",
            "negative": "âm",
        }[direction]

        strength_text = {
            "moderate": "trung bình",
            "strong": "mạnh",
            "very_strong": "rất mạnh",
        }[strength]

        if direction == "positive":
            trend_description = (
                f"Khi {first_column} tăng, "
                f"{second_column} có xu hướng tăng theo."
            )
        else:
            trend_description = (
                f"Khi {first_column} tăng, "
                f"{second_column} có xu hướng giảm."
            )

        return InsightObject(
            id=(
                f"correlation_"
                f"{safe_first_column}_"
                f"{safe_second_column}"
            ),
            type=insight_type,
            category="correlation",
            title=(
                f"{first_column} và "
                f"{second_column} có tương quan "
                f"{direction_text} {strength_text}"
            ),
            description=(
                f"{first_column} có tương quan "
                f"{direction_text} {strength_text} "
                f"với {second_column}, với hệ số "
                f"tương quan Pearson "
                f"r = {display_coefficient}. "
                f"{trend_description} "
                f"Tương quan không đồng nghĩa "
                f"với quan hệ nhân quả."
            ),
            metric="pearson_correlation",
            value=rounded_coefficient,
            unit=None,
            threshold=(
                f"|r| >= "
                f"{self.MIN_CORRELATION}"
            ),
            severity=severity,
            evidence=InsightEvidence(
                column=first_column,
                related_columns=[
                    second_column,
                ],
                affected_rows=None,
                total_rows=None,
                calculation=(
                    f"Pearson correlation("
                    f"{first_column}, "
                    f"{second_column}) "
                    f"= {rounded_coefficient}"
                ),
                sample_values=[],
            ),
            metadata={
                "first_column": first_column,
                "second_column": second_column,
                "correlation_coefficient": (
                    rounded_coefficient
                ),
                "absolute_correlation": round(
                    abs(coefficient),
                    4,
                ),
                "direction": direction,
                "strength": strength,
                "method": "pearson",
                "detector": "CorrelationDetector",
                "causation_warning": True,
            },
        )

    def _get_direction(
        self,
        coefficient: float,
    ) -> str:

        if coefficient >= 0:
            return "positive"

        return "negative"

    def _get_strength(
        self,
        coefficient: float,
    ) -> str:

        absolute_value = abs(coefficient)

        if (
            absolute_value
            >= self.VERY_STRONG_THRESHOLD
        ):
            return "very_strong"

        if (
            absolute_value
            >= self.STRONG_THRESHOLD
        ):
            return "strong"

        return "moderate"

    def _get_severity(
        self,
        coefficient: float,
    ) -> InsightSeverity:

        absolute_value = abs(coefficient)

        if (
            absolute_value
            >= self.VERY_STRONG_THRESHOLD
        ):
            return InsightSeverity.HIGH

        if (
            absolute_value
            >= self.STRONG_THRESHOLD
        ):
            return InsightSeverity.MEDIUM

        return InsightSeverity.LOW

    def _get_type(
        self,
        coefficient: float,
    ) -> InsightType:
        """
        Tương quan dương dùng POSITIVE.

        Tương quan âm dùng INFORMATION vì tương quan âm
        không nhất thiết là vấn đề hoặc cảnh báo.
        """

        if coefficient > 0:
            return InsightType.POSITIVE

        return InsightType.INFORMATION

    def _is_id_column(
        self,
        column_name: str,
    ) -> bool:

        normalized_name = (
            column_name.strip().lower()
        )

        if normalized_name in {
            "id",
            "index",
            "no",
            "number",
        }:
            return True

        id_suffixes = (
            "_id",
            "_code",
            "_number",
            "_no",
        )

        return normalized_name.endswith(
            id_suffixes
        )

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