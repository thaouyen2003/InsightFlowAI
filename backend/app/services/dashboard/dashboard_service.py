from typing import Any

import pandas as pd

from app.services.dashboard.chart_generator import ChartGenerator
from app.services.dashboard.data_cleaner import DataCleaner
from app.services.dashboard.data_context_builder import DataContextBuilder
from app.services.dashboard.dataset_classifier import DatasetClassifier
from app.services.dashboard.kpi_generator import KPIGenerator


class DashboardService:
    """
    Điều phối pipeline tạo dashboard.

    Pipeline:
    1. Phân tích dữ liệu ban đầu.
    2. Làm sạch dữ liệu.
    3. Phân tích lại dữ liệu đã làm sạch.
    4. Phân loại dataset.
    5. Tạo KPI.
    6. Tạo biểu đồ.
    """

    def __init__(self):
        self.data_cleaner = DataCleaner()
        self.data_context_builder = DataContextBuilder()
        self.dataset_classifier = DatasetClassifier()
        self.kpi_generator = KPIGenerator()
        self.chart_generator = ChartGenerator()

    def generate(
        self,
        df: pd.DataFrame,
    ) -> dict[str, Any]:
        # 1. Phân tích metadata trước khi làm sạch
        initial_context = self.data_context_builder.build(df)

        # 2. Làm sạch dữ liệu dựa trên metadata ban đầu
        cleaned_df, cleaning_warnings = self.data_cleaner.clean(
            df=df,
            columns_metadata=initial_context["columns"],
        )

        # 3. Phân tích lại metadata sau khi làm sạch
        data_context = self.data_context_builder.build(
            cleaned_df
        )

        # 4. Phân loại loại dataset
        dataset_profile = self.dataset_classifier.classify(
            data_context
        )

        # 5. Tạo KPI từ dữ liệu đã làm sạch
        kpis, kpi_warnings = self._safe_generate_kpis(
            df=cleaned_df,
            data_context=data_context,
            dataset_profile=dataset_profile,
        )

        # 6. Tạo biểu đồ từ dữ liệu đã làm sạch
        charts, chart_warnings = self._safe_generate_charts(
            cleaned_df
        )

        # 7. Gộp toàn bộ cảnh báo
        warnings = [
            *data_context.get("warnings", []),
            *cleaning_warnings,
            *kpi_warnings,
            *chart_warnings,
        ]

        status = self._determine_status(
            kpis=kpis,
            charts=charts,
            warnings=warnings,
        )

        return {
            "success": True,
            "status": status,
            "summary": {
                "rows": int(len(cleaned_df)),
                "columns": int(len(cleaned_df.columns)),
            },
            "cleaning_summary": {
                "processed_columns": int(
                    len(cleaned_df.columns)
                ),
                "warning_count": int(
                    len(cleaning_warnings)
                ),
            },
            "dataset_profile": dataset_profile,
            "data_context": data_context,
            "kpis": kpis,
            "charts": charts,
            "warnings": warnings,
        }

    def _safe_generate_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, str]],
    ]:
        try:
            result = self.kpi_generator.generate(
                df=df,
                data_context=data_context,
                dataset_profile=dataset_profile,
            )

            if not isinstance(result, list):
                return [], [{
                    "type": "invalid_kpi_result",
                    "message": (
                        "KPIGenerator không trả về "
                        "danh sách KPI hợp lệ."
                    ),
                }]

            return result, []

        except Exception as error:
            print(
                "KPI generation failed:",
                str(error),
            )

            return [], [{
                "type": "kpi_generation_failed",
                "message": (
                    "Không thể tạo KPI: "
                    f"{str(error)}"
                ),
            }]
    def _safe_generate_charts(
        self,
        df: pd.DataFrame,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, str]],
    ]:
        try:
            result = self.chart_generator.generate(df)

            if not isinstance(result, list):
                return [], [{
                    "type": "invalid_chart_result",
                    "message": (
                        "ChartGenerator không trả về "
                        "danh sách biểu đồ hợp lệ."
                    ),
                }]

            return result, []

        except Exception as error:
            print(
                "Chart generation failed:",
                str(error),
            )

            return [], [{
                "type": "chart_generation_failed",
                "message": (
                    "Không thể tạo biểu đồ: "
                    f"{str(error)}"
                ),
            }]

    def _determine_status(
        self,
        kpis: list[dict[str, Any]],
        charts: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> str:
        if kpis and charts and not warnings:
            return "complete"

        if kpis or charts:
            return "partial"

        return "insufficient_data"