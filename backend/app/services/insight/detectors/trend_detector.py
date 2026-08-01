import re

import numpy as np
import pandas as pd

from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)


class TrendDetector:
    """
    Phát hiện xu hướng tăng hoặc giảm của biến số
    theo thời gian.

    Không gọi LLM.
    Không thay đổi DataFrame gốc.
    Chỉ sinh InsightObject.
    """

    MIN_DATA_POINTS = 4
    MIN_CHANGE_PERCENT = 5.0
    MAX_RESULTS = 10

    def detect(
        self,
        df: pd.DataFrame,
    ) -> list[InsightObject]:

        if df.empty:
            return []

        datetime_columns = (
            self._detect_datetime_columns(df)
        )

        numeric_columns = (
            self._detect_numeric_columns(df)
        )

        if not datetime_columns:
            return []

        if not numeric_columns:
            return []

        insights: list[InsightObject] = []

        for datetime_column in datetime_columns:
            for numeric_column in numeric_columns:
                insight = self._analyze_trend(
                    df=df,
                    datetime_column=datetime_column,
                    numeric_column=numeric_column,
                )

                if insight is not None:
                    insights.append(insight)

        return sorted(
            insights,
            key=lambda item: abs(
                float(item.metadata.get(
                    "change_percent",
                    0,
                ))
            ),
            reverse=True,
        )[: self.MAX_RESULTS]

    def _detect_datetime_columns(
        self,
        df: pd.DataFrame,
    ) -> list[str]:
        """
        Phát hiện các cột thời gian.

        Hỗ trợ:
        - datetime dtype
        - chuỗi có thể chuyển thành datetime
        """

        datetime_columns: list[str] = []

        for column in df.columns:
            series = df[column]

            if pd.api.types.is_datetime64_any_dtype(
                series
            ):
                datetime_columns.append(
                    str(column)
                )
                continue

            if not (
                pd.api.types.is_object_dtype(series)
                or pd.api.types.is_string_dtype(series)
            ):
                continue

            non_null_values = series.dropna()

            if non_null_values.empty:
                continue

            parsed_values = pd.to_datetime(
                non_null_values,
                errors="coerce",
            )

            success_rate = float(
                parsed_values.notna().mean()
            )

            if success_rate >= 0.80:
                datetime_columns.append(
                    str(column)
                )

        return datetime_columns

    def _detect_numeric_columns(
        self,
        df: pd.DataFrame,
    ) -> list[str]:
        """
        Lấy các cột số hợp lệ.

        Loại bỏ:
        - Cột ID
        - Cột hằng số
        - Cột hoàn toàn rỗng
        """

        numeric_columns: list[str] = []

        numeric_df = df.select_dtypes(
            include="number",
        )

        for column in numeric_df.columns:
            column_name = str(column)

            if self._is_id_column(
                column_name
            ):
                continue

            non_null_values = numeric_df[
                column
            ].dropna()

            if non_null_values.empty:
                continue

            if non_null_values.nunique() <= 1:
                continue

            numeric_columns.append(
                column_name
            )

        return numeric_columns

    def _analyze_trend(
        self,
        df: pd.DataFrame,
        datetime_column: str,
        numeric_column: str,
    ) -> InsightObject | None:

        trend_df = df[
            [
                datetime_column,
                numeric_column,
            ]
        ].copy()

        trend_df[datetime_column] = pd.to_datetime(
            trend_df[datetime_column],
            errors="coerce",
        )

        trend_df[numeric_column] = pd.to_numeric(
            trend_df[numeric_column],
            errors="coerce",
        )

        trend_df = trend_df.dropna()

        if len(trend_df) < self.MIN_DATA_POINTS:
            return None

        trend_df = trend_df.sort_values(
            by=datetime_column
        )

        aggregated_df = (
            trend_df.groupby(
                datetime_column,
                as_index=False,
            )[numeric_column]
            .mean()
            .sort_values(
                by=datetime_column
            )
        )

        if (
            len(aggregated_df)
            < self.MIN_DATA_POINTS
        ):
            return None

        values = aggregated_df[
            numeric_column
        ].to_numpy(
            dtype=float
        )

        first_value = float(values[0])
        last_value = float(values[-1])

        if first_value == 0:
            absolute_change = (
                last_value - first_value
            )

            change_percent = 0.0
        else:
            absolute_change = (
                last_value - first_value
            )

            change_percent = (
                absolute_change
                / abs(first_value)
                * 100
            )

        if (
            abs(change_percent)
            < self.MIN_CHANGE_PERCENT
        ):
            return None

        x_values = np.arange(
            len(values),
            dtype=float,
        )

        slope = float(
            np.polyfit(
                x_values,
                values,
                1,
            )[0]
        )

        if slope > 0:
            direction = "increasing"
        elif slope < 0:
            direction = "decreasing"
        else:
            return None

        return self._build_insight(
            datetime_column=datetime_column,
            numeric_column=numeric_column,
            first_value=first_value,
            last_value=last_value,
            absolute_change=absolute_change,
            change_percent=change_percent,
            slope=slope,
            direction=direction,
            data_points=len(aggregated_df),
            start_date=aggregated_df[
                datetime_column
            ].iloc[0],
            end_date=aggregated_df[
                datetime_column
            ].iloc[-1],
        )

    def _build_insight(
        self,
        datetime_column: str,
        numeric_column: str,
        first_value: float,
        last_value: float,
        absolute_change: float,
        change_percent: float,
        slope: float,
        direction: str,
        data_points: int,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> InsightObject:

        safe_datetime_column = self._slugify(
            datetime_column
        )

        safe_numeric_column = self._slugify(
            numeric_column
        )

        severity = self._get_severity(
            change_percent
        )

        rounded_change_percent = round(
            change_percent,
            2,
        )

        rounded_absolute_change = round(
            absolute_change,
            4,
        )

        rounded_first_value = round(
            first_value,
            4,
        )

        rounded_last_value = round(
            last_value,
            4,
        )

        rounded_slope = round(
            slope,
            6,
        )

        if direction == "increasing":
            direction_text = "tăng"

            insight_type = (
                InsightType.POSITIVE
            )
        else:
            direction_text = "giảm"

            insight_type = (
                InsightType.WARNING
            )

        return InsightObject(
            id=(
                f"trend_"
                f"{safe_datetime_column}_"
                f"{safe_numeric_column}"
            ),
            type=insight_type,
            category="trend",
            title=(
                f"{numeric_column} có xu hướng "
                f"{direction_text} theo thời gian"
            ),
            description=(
                f"{numeric_column} có xu hướng "
                f"{direction_text} theo "
                f"{datetime_column}. "
                f"Giá trị thay đổi từ "
                f"{rounded_first_value} thành "
                f"{rounded_last_value}, "
                f"tương đương "
                f"{rounded_change_percent}%. "
                f"Xu hướng được xác định từ "
                f"{data_points} mốc thời gian."
            ),
            metric="trend_change_percent",
            value=rounded_change_percent,
            unit="%",
            threshold=(
                f"|change| >= "
                f"{self.MIN_CHANGE_PERCENT}%"
            ),
            severity=severity,
            evidence=InsightEvidence(
                column=numeric_column,
                related_columns=[
                    datetime_column,
                ],
                affected_rows=data_points,
                total_rows=data_points,
                calculation=(
                    f"({rounded_last_value} - "
                    f"{rounded_first_value}) / "
                    f"|{rounded_first_value}| "
                    f"* 100 = "
                    f"{rounded_change_percent}%"
                ),
                sample_values=[
                    rounded_first_value,
                    rounded_last_value,
                ],
            ),
            metadata={
                "datetime_column": (
                    datetime_column
                ),
                "numeric_column": numeric_column,
                "direction": direction,
                "first_value": (
                    rounded_first_value
                ),
                "last_value": (
                    rounded_last_value
                ),
                "absolute_change": (
                    rounded_absolute_change
                ),
                "change_percent": (
                    rounded_change_percent
                ),
                "slope": rounded_slope,
                "data_points": data_points,
                "start_date": (
                    start_date.isoformat()
                ),
                "end_date": (
                    end_date.isoformat()
                ),
                "aggregation": "mean",
                "detector": "TrendDetector",
            },
        )

    def _get_severity(
        self,
        change_percent: float,
    ) -> InsightSeverity:

        absolute_change = abs(
            change_percent
        )

        if absolute_change >= 50:
            return InsightSeverity.CRITICAL

        if absolute_change >= 25:
            return InsightSeverity.HIGH

        if absolute_change >= 10:
            return InsightSeverity.MEDIUM

        return InsightSeverity.LOW

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