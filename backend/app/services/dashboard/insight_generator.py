from typing import Any

import pandas as pd


class InsightGenerator:
    """
    Sinh insight định lượng từ kết quả dashboard.

    Nguyên tắc:
    - Insight phải dựa trên số liệu backend đã tính.
    - Không để LLM tự tính toán từ dữ liệu thô.
    - Mỗi insight có evidence để kiểm chứng.
    - Không tạo insight nếu dữ liệu không đủ tin cậy.
    """

    MAX_INSIGHTS = 6
    MAX_RECOMMENDATIONS = 4

    def generate(
        self,
        df: pd.DataFrame,
        kpis: list[dict[str, Any]],
        charts: list[dict[str, Any]],
        data_context: dict[str, Any],
        dataset_profile: dict[str, Any],
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        insights: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        insights.extend(
            self._generate_dataset_overview(
                df=df,
                dataset_profile=dataset_profile,
            )
        )

        insights.extend(
            self._generate_kpi_insights(
                kpis=kpis,
            )
        )

        insights.extend(
            self._generate_trend_insights(
                charts=charts,
            )
        )

        insights.extend(
            self._generate_category_insights(
                charts=charts,
            )
        )

        insights.extend(
            self._generate_data_quality_insights(
                warnings=warnings,
                data_context=data_context,
            )
        )

        insights = self._remove_duplicate_insights(
            insights
        )

        insights = sorted(
            insights,
            key=lambda item: item.get(
                "priority",
                0,
            ),
            reverse=True,
        )[:self.MAX_INSIGHTS]

        recommendations.extend(
            self._build_recommendations(
                insights=insights,
                dataset_type=dataset_profile.get(
                    "dataset_type",
                    "generic",
                ),
            )
        )

        return {
            "insights": insights,
            "recommendations": (
                recommendations[
                    :self.MAX_RECOMMENDATIONS
                ]
            ),
            "summary": {
                "insight_count": len(insights),
                "recommendation_count": len(
                    recommendations[
                        :self.MAX_RECOMMENDATIONS
                    ]
                ),
                "generation_method": (
                    "statistical_rule_based"
                ),
            },
        }

    def _generate_dataset_overview(
        self,
        df: pd.DataFrame,
        dataset_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        dataset_type = dataset_profile.get(
            "dataset_type",
            "generic",
        )

        confidence = dataset_profile.get(
            "confidence",
            0,
        )

        return [{
            "id": "dataset_overview",
            "type": "overview",
            "title": "Dataset Overview",
            "description": (
                f"Hệ thống nhận diện đây là dataset "
                f"thuộc nhóm {dataset_type}, gồm "
                f"{len(df):,} dòng và "
                f"{len(df.columns)} cột."
            ),
            "severity": "neutral",
            "priority": 20,
            "evidence": {
                "dataset_type": dataset_type,
                "confidence": confidence,
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
            },
        }]

    def _generate_kpi_insights(
        self,
        kpis: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        for kpi in kpis[:4]:
            title = str(
                kpi.get("title", "")
            )

            value = kpi.get("value")
            kpi_format = kpi.get(
                "format",
                "number",
            )

            if not title or value is None:
                continue

            formatted_value = (
                self._format_value(
                    value=value,
                    value_format=kpi_format,
                )
            )

            insights.append({
                "id": (
                    "kpi_"
                    + str(
                        kpi.get(
                            "id",
                            title,
                        )
                    )
                ),
                "type": "kpi",
                "title": title,
                "description": (
                    f"{title} hiện đạt "
                    f"{formatted_value}."
                ),
                "severity": "neutral",
                "priority": int(
                    kpi.get(
                        "priority",
                        40,
                    )
                ),
                "evidence": {
                    "value": value,
                    "format": kpi_format,
                    "column": kpi.get(
                        "column"
                    ),
                    "aggregation": kpi.get(
                        "aggregation"
                    ),
                },
            })

        return insights

    def _generate_trend_insights(
        self,
        charts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        line_charts = [
            chart
            for chart in charts
            if chart.get("type") == "line"
        ]

        for chart in line_charts[:2]:
            data = chart.get("data", [])

            valid_points = [
                point
                for point in data
                if self._is_number(
                    point.get("y")
                )
            ]

            if len(valid_points) < 2:
                continue

            first_value = float(
                valid_points[0]["y"]
            )

            last_value = float(
                valid_points[-1]["y"]
            )

            absolute_change = (
                last_value - first_value
            )

            percentage_change = (
                absolute_change
                / abs(first_value)
                * 100
                if first_value != 0
                else None
            )

            if percentage_change is None:
                continue

            if percentage_change > 1:
                direction = "tăng"
                severity = "positive"
            elif percentage_change < -1:
                direction = "giảm"
                severity = "negative"
            else:
                direction = "ổn định"
                severity = "neutral"

            measure_name = (
                chart.get("y_axis")
                or chart.get("measure")
                or "Chỉ số"
            )

            insights.append({
                "id": (
                    f"trend_{chart.get('id')}"
                ),
                "type": "trend",
                "title": (
                    f"{self._format_name(measure_name)} "
                    "Trend"
                ),
                "description": (
                    f"{self._format_name(measure_name)} "
                    f"{direction} "
                    f"{abs(percentage_change):.2f}% "
                    "từ kỳ đầu đến kỳ gần nhất."
                ),
                "severity": severity,
                "priority": 100,
                "evidence": {
                    "first_value": (
                        self._json_number(
                            first_value
                        )
                    ),
                    "last_value": (
                        self._json_number(
                            last_value
                        )
                    ),
                    "absolute_change": (
                        self._json_number(
                            absolute_change
                        )
                    ),
                    "percentage_change": round(
                        percentage_change,
                        2,
                    ),
                    "first_period": (
                        valid_points[0].get("x")
                    ),
                    "last_period": (
                        valid_points[-1].get("x")
                    ),
                    "chart_id": chart.get("id"),
                },
            })

        return insights

    def _generate_category_insights(
        self,
        charts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        categorical_charts = [
            chart
            for chart in charts
            if chart.get("type") in {
                "bar",
                "pie",
            }
        ]

        used_pairs: set[
            tuple[Any, Any]
        ] = set()

        for chart in categorical_charts:
            pair = (
                chart.get("dimension"),
                chart.get("measure"),
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            normalized_data = (
                self._normalize_category_data(
                    chart
                )
            )

            if not normalized_data:
                continue

            sorted_data = sorted(
                normalized_data,
                key=lambda item: item[
                    "value"
                ],
                reverse=True,
            )

            top_item = sorted_data[0]

            total_value = sum(
                item["value"]
                for item in sorted_data
            )

            share = (
                top_item["value"]
                / total_value
                * 100
                if total_value != 0
                else 0
            )

            dimension = (
                chart.get("dimension")
                or "category"
            )

            measure = (
                chart.get("measure")
                or "value"
            )

            severity = (
                "warning"
                if share >= 60
                else "neutral"
            )

            insights.append({
                "id": (
                    f"top_category_"
                    f"{dimension}_{measure}"
                ),
                "type": "contribution",
                "title": (
                    f"Top "
                    f"{self._format_name(dimension)}"
                ),
                "description": (
                    f"{top_item['label']} là nhóm "
                    f"dẫn đầu về "
                    f"{self._format_name(measure)}, "
                    f"chiếm {share:.2f}% "
                    "tổng giá trị trong biểu đồ."
                ),
                "severity": severity,
                "priority": 90,
                "evidence": {
                    "top_category": (
                        top_item["label"]
                    ),
                    "top_value": (
                        self._json_number(
                            top_item["value"]
                        )
                    ),
                    "share_percentage": round(
                        share,
                        2,
                    ),
                    "dimension": dimension,
                    "measure": measure,
                    "chart_id": chart.get("id"),
                },
            })

        return insights

    def _generate_data_quality_insights(
        self,
        warnings: list[dict[str, Any]],
        data_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        quality_warnings = [
            warning
            for warning in warnings
            if warning.get("type") in {
                "high_missing_values",
                "empty_dataset",
                "no_measure",
                "no_dimension",
                "cleaning_failed",
                "numeric_conversion_skipped",
                "datetime_conversion_skipped",
            }
        ]

        if quality_warnings:
            insights.append({
                "id": "data_quality_warning",
                "type": "data_quality",
                "title": "Data Quality Attention",
                "description": (
                    f"Hệ thống phát hiện "
                    f"{len(quality_warnings)} vấn đề "
                    "có thể ảnh hưởng đến độ chính xác "
                    "của dashboard."
                ),
                "severity": "warning",
                "priority": 85,
                "evidence": {
                    "warning_count": len(
                        quality_warnings
                    ),
                    "warning_types": [
                        warning.get("type")
                        for warning
                        in quality_warnings
                    ],
                },
            })

        missing_columns = [
            column
            for column in data_context.get(
                "columns",
                [],
            )
            if column.get(
                "missing_percentage",
                0,
            ) > 0
        ]

        if missing_columns:
            highest_missing = max(
                missing_columns,
                key=lambda column: column.get(
                    "missing_percentage",
                    0,
                ),
            )

            insights.append({
                "id": "highest_missing_column",
                "type": "data_quality",
                "title": "Missing Data",
                "description": (
                    f"Cột "
                    f"{highest_missing.get('name')} "
                    f"có tỷ lệ thiếu cao nhất, "
                    f"đạt "
                    f"{highest_missing.get('missing_percentage')}%."
                ),
                "severity": "warning",
                "priority": 70,
                "evidence": {
                    "column": highest_missing.get(
                        "name"
                    ),
                    "missing_percentage": (
                        highest_missing.get(
                            "missing_percentage"
                        )
                    ),
                },
            })

        return insights

    def _build_recommendations(
        self,
        insights: list[dict[str, Any]],
        dataset_type: str,
    ) -> list[dict[str, Any]]:
        recommendations: list[
            dict[str, Any]
        ] = []

        negative_trends = [
            insight
            for insight in insights
            if (
                insight.get("type")
                == "trend"
                and insight.get("severity")
                == "negative"
            )
        ]

        for insight in negative_trends:
            recommendations.append({
                "id": (
                    f"recommend_"
                    f"{insight.get('id')}"
                ),
                "title": "Investigate Declining Trend",
                "description": (
                    "Phân tích sâu theo khu vực, "
                    "sản phẩm, kênh bán hàng và "
                    "thời gian để xác định nguyên nhân "
                    "của xu hướng giảm."
                ),
                "priority": "high",
                "related_insight_id": (
                    insight.get("id")
                ),
            })

        concentration_insights = [
            insight
            for insight in insights
            if (
                insight.get("type")
                == "contribution"
                and insight.get(
                    "evidence",
                    {},
                ).get(
                    "share_percentage",
                    0,
                )
                >= 60
            )
        ]

        for insight in concentration_insights:
            recommendations.append({
                "id": (
                    f"recommend_"
                    f"{insight.get('id')}"
                ),
                "title": "Reduce Concentration Risk",
                "description": (
                    "Theo dõi mức phụ thuộc vào nhóm "
                    "đang đóng góp tỷ trọng lớn và "
                    "xem xét đa dạng hóa các nhóm còn lại."
                ),
                "priority": "medium",
                "related_insight_id": (
                    insight.get("id")
                ),
            })

        has_quality_warning = any(
            insight.get("type")
            == "data_quality"
            for insight in insights
        )

        if has_quality_warning:
            recommendations.append({
                "id": "recommend_data_quality",
                "title": "Improve Data Quality",
                "description": (
                    "Kiểm tra giá trị thiếu, định dạng "
                    "không đồng nhất và các cột chuyển "
                    "đổi thất bại trước khi dùng kết quả "
                    "cho quyết định quan trọng."
                ),
                "priority": "high",
                "related_insight_id": (
                    "data_quality_warning"
                ),
            })

        if (
            not recommendations
            and dataset_type == "sales"
        ):
            recommendations.append({
                "id": "recommend_sales_monitoring",
                "title": "Monitor Business Drivers",
                "description": (
                    "Theo dõi doanh thu, số đơn hàng, "
                    "giá trị đơn trung bình và nhóm "
                    "sản phẩm dẫn đầu theo từng kỳ."
                ),
                "priority": "medium",
                "related_insight_id": None,
            })

        if not recommendations:
            recommendations.append({
                "id": "recommend_general_monitoring",
                "title": "Continue Monitoring",
                "description": (
                    "Tiếp tục theo dõi các KPI và "
                    "cập nhật dữ liệu định kỳ để phát "
                    "hiện thay đổi đáng chú ý."
                ),
                "priority": "low",
                "related_insight_id": None,
            })

        return recommendations

    def _normalize_category_data(
        self,
        chart: dict[str, Any],
    ) -> list[dict[str, Any]]:
        data = chart.get("data", [])

        normalized: list[
            dict[str, Any]
        ] = []

        for item in data:
            label = (
                item.get("label")
                or item.get("name")
            )

            value = item.get("value")

            if (
                label is None
                or not self._is_number(value)
            ):
                continue

            normalized.append({
                "label": str(label),
                "value": float(value),
            })

        return normalized

    def _remove_duplicate_insights(
        self,
        insights: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique_insights: list[
            dict[str, Any]
        ] = []

        used_ids: set[str] = set()

        for insight in insights:
            insight_id = str(
                insight.get("id", "")
            )

            if not insight_id:
                continue

            if insight_id in used_ids:
                continue

            used_ids.add(insight_id)
            unique_insights.append(insight)

        return unique_insights

    def _format_value(
        self,
        value: Any,
        value_format: str,
    ) -> str:
        if not self._is_number(value):
            return str(value)

        numeric_value = float(value)

        if value_format == "percentage":
            return f"{numeric_value:,.2f}%"

        if value_format == "currency":
            return f"{numeric_value:,.2f}"

        if numeric_value.is_integer():
            return f"{int(numeric_value):,}"

        return f"{numeric_value:,.2f}"

    def _format_name(
        self,
        value: str,
    ) -> str:
        return (
            value
            .replace("_", " ")
            .strip()
            .title()
        )

    def _is_number(
        self,
        value: Any,
    ) -> bool:
        if isinstance(
            value,
            (int, float),
        ):
            return not pd.isna(value)

        return False

    def _json_number(
        self,
        value: Any,
    ) -> int | float:
        number = float(value)

        if number.is_integer():
            return int(number)

        return round(number, 2)