import pandas as pd

from app.services.insight.insight_models import (
    InsightEvidence,
    InsightObject,
    InsightSeverity,
    InsightType,
)


class CategoryDetector:
    """
    Phát hiện các pattern đáng chú ý trong cột phân loại.

    Detector hiện tại phát hiện:

    1. Nhóm chiếm ưu thế
    2. Phân phối mất cân bằng
    3. Nhóm có tần suất rất thấp
    """

    MAX_UNIQUE_CATEGORIES = 30

    DOMINANT_THRESHOLD = 0.60
    HIGH_DOMINANT_THRESHOLD = 0.80
    CRITICAL_DOMINANT_THRESHOLD = 0.95

    RARE_CATEGORY_THRESHOLD = 0.05

    def detect(
        self,
        df: pd.DataFrame,
        data_context: dict | None = None,
    ) -> list[InsightObject]:
        """
        Phân tích các cột categorical trong DataFrame.
        """

        if df.empty:
            return []

        category_columns = (
            self._get_category_columns(
                df=df,
                data_context=data_context,
            )
        )

        insights: list[InsightObject] = []

        for column in category_columns:
            series = df[column].dropna()

            if series.empty:
                continue

            value_counts = series.value_counts()

            if len(value_counts) < 2:
                continue

            insights.extend(
                self._detect_dominant_category(
                    column=column,
                    value_counts=value_counts,
                )
            )

            insights.extend(
                self._detect_rare_categories(
                    column=column,
                    value_counts=value_counts,
                )
            )

        return insights

    def _get_category_columns(
        self,
        df: pd.DataFrame,
        data_context: dict | None,
    ) -> list[str]:
        """
        Chọn các cột categorical phù hợp.

        Loại bỏ:

        - Cột có quá nhiều giá trị duy nhất
        - Cột có dấu hiệu là ID
        - Cột chỉ có một giá trị
        """

        category_columns: list[str] = []

        for column in df.columns:
            series = df[column]

            if pd.api.types.is_numeric_dtype(series):
                continue

            if pd.api.types.is_datetime64_any_dtype(
                series
            ):
                continue

            unique_count = int(
                series.nunique(
                    dropna=True
                )
            )

            if unique_count < 2:
                continue

            if (
                unique_count
                > self.MAX_UNIQUE_CATEGORIES
            ):
                continue

            if self._looks_like_id_column(
                column=column,
                series=series,
            ):
                continue

            category_columns.append(column)

        return category_columns

    def _looks_like_id_column(
        self,
        column: str,
        series: pd.Series,
    ) -> bool:
        """
        Phát hiện cột có khả năng là mã định danh.
        """

        column_lower = column.lower()

        id_keywords = (
            "_id",
            "id_",
            "uuid",
            "code",
            "identifier",
        )

        if (
            column_lower == "id"
            or column_lower.endswith("_id")
            or column_lower.startswith("id_")
        ):
            return True

        if any(
            keyword in column_lower
            for keyword in id_keywords
        ):
            return True

        non_null_count = int(
            series.notna().sum()
        )

        if non_null_count == 0:
            return False

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        uniqueness_ratio = (
            unique_count / non_null_count
        )

        return uniqueness_ratio >= 0.95

    def _detect_dominant_category(
        self,
        column: str,
        value_counts: pd.Series,
    ) -> list[InsightObject]:
        """
        Phát hiện nhóm chiếm tỷ trọng lớn.
        """

        total_values = int(
            value_counts.sum()
        )

        dominant_category = str(
            value_counts.index[0]
        )

        dominant_count = int(
            value_counts.iloc[0]
        )

        dominant_rate = (
            dominant_count / total_values
        )

        if (
            dominant_rate
            < self.DOMINANT_THRESHOLD
        ):
            return []

        dominant_percent = round(
            dominant_rate * 100,
            2,
        )

        severity = (
            self._get_dominant_severity(
                dominant_rate
            )
        )

        insight = InsightObject(
            id=(
                f"category_dominant_"
                f"{column}"
            ),
            type=InsightType.WARNING,
            category="category_analysis",
            title=(
                f"Cột {column} có một nhóm "
                f"chiếm ưu thế"
            ),
            description=(
                f"Nhóm '{dominant_category}' "
                f"xuất hiện {dominant_count} lần "
                f"trong cột {column}, chiếm "
                f"{dominant_percent}% số giá trị "
                f"hợp lệ."
            ),
            metric="dominant_category_rate",
            value=dominant_percent,
            unit="%",
            threshold=(
                f">= "
                f"{self.DOMINANT_THRESHOLD * 100}%"
            ),
            severity=severity,
            evidence=InsightEvidence(
                affected_rows=dominant_count,
                total_rows=total_values,
                calculation=(
                    f"{dominant_count} / "
                    f"{total_values} * 100 "
                    f"= {dominant_percent}%"
                ),
            ),
            metadata={
                "column": column,
                "dominant_category": (
                    dominant_category
                ),
                "dominant_count": dominant_count,
                "dominant_rate": round(
                    dominant_rate,
                    4,
                ),
                "unique_categories": len(
                    value_counts
                ),
                "detector": "CategoryDetector",
            },
        )

        return [insight]

    def _detect_rare_categories(
        self,
        column: str,
        value_counts: pd.Series,
    ) -> list[InsightObject]:
        """
        Phát hiện các nhóm có tỷ lệ dưới ngưỡng.
        """

        total_values = int(
            value_counts.sum()
        )

        category_rates = (
            value_counts / total_values
        )

        rare_rates = category_rates[
            category_rates
            < self.RARE_CATEGORY_THRESHOLD
        ]

        if rare_rates.empty:
            return []

        rare_categories = [
            str(category)
            for category in rare_rates.index
        ]

        rare_count = int(
            value_counts.loc[
                rare_rates.index
            ].sum()
        )

        rare_percent = round(
            rare_count
            / total_values
            * 100,
            2,
        )

        rare_category_details = {
            str(category): {
                "count": int(
                    value_counts.loc[
                        category
                    ]
                ),
                "rate": round(
                    float(
                        category_rates.loc[
                            category
                        ]
                    )
                    * 100,
                    2,
                ),
            }
            for category in rare_rates.index
        }

        category_text = ", ".join(
            rare_categories[:5]
        )

        if len(rare_categories) > 5:
            category_text += ", ..."

        severity = (
            InsightSeverity.MEDIUM
            if len(rare_categories) >= 3
            else InsightSeverity.LOW
        )

        insight = InsightObject(
            id=(
                f"category_rare_"
                f"{column}"
            ),
            type=InsightType.WARNING,
            category="category_analysis",
            title=(
                f"Cột {column} có nhóm "
                f"tần suất thấp"
            ),
            description=(
                f"Phát hiện {len(rare_categories)} "
                f"nhóm hiếm trong cột {column}: "
                f"{category_text}. Tổng cộng các "
                f"nhóm này chiếm {rare_percent}% "
                f"số giá trị hợp lệ."
            ),
            metric="rare_category_rate",
            value=rare_percent,
            unit="%",
            threshold=(
                f"Mỗi nhóm < "
                f"{self.RARE_CATEGORY_THRESHOLD * 100}%"
            ),
            severity=severity,
            evidence=InsightEvidence(
                affected_rows=rare_count,
                total_rows=total_values,
                calculation=(
                    f"{rare_count} / "
                    f"{total_values} * 100 "
                    f"= {rare_percent}%"
                ),
            ),
            metadata={
                "column": column,
                "rare_categories": (
                    rare_category_details
                ),
                "rare_category_count": len(
                    rare_categories
                ),
                "unique_categories": len(
                    value_counts
                ),
                "detector": "CategoryDetector",
            },
        )

        return [insight]

    def _get_dominant_severity(
        self,
        dominant_rate: float,
    ) -> InsightSeverity:
        """
        Xác định severity dựa trên tỷ lệ
        nhóm chiếm ưu thế.
        """

        if (
            dominant_rate
            >= self.CRITICAL_DOMINANT_THRESHOLD
        ):
            return InsightSeverity.CRITICAL

        if (
            dominant_rate
            >= self.HIGH_DOMINANT_THRESHOLD
        ):
            return InsightSeverity.HIGH

        return InsightSeverity.MEDIUM