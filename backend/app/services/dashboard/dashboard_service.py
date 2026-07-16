from typing import Any

import pandas as pd

from app.services.dashboard.chart_generator import ChartGenerator
from app.services.dashboard.data_context_builder import DataContextBuilder
from app.services.dashboard.kpi_generator import KPIGenerator


class DashboardService:
    """
    Điều phối quá trình tạo dashboard.

    Pipeline hiện tại:
    1. Phân tích semantic và xây dựng data context.
    2. Tạo KPI bằng KPIGenerator hiện tại.
    3. Tạo biểu đồ bằng ChartGenerator hiện tại.
    4. Không để lỗi KPI hoặc chart làm toàn bộ dashboard thất bại.
    """

    def __init__(self):
        self.data_context_builder = DataContextBuilder()
        self.kpi_generator = KPIGenerator()
        self.chart_generator = ChartGenerator()

    def generate(
        self,
        df: pd.DataFrame,
    ) -> dict[str, Any]:
        data_context = self.data_context_builder.build(df)

        kpis, kpi_warnings = self._safe_generate_kpis(df)
        charts, chart_warnings = self._safe_generate_charts(df)

        warnings = [
            *data_context.get("warnings", []),
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
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
            },
            "data_context": data_context,
            "kpis": kpis,
            "charts": charts,
            "warnings": warnings,
        }

    def _safe_generate_kpis(
        self,
        df: pd.DataFrame,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        try:
            result = self.kpi_generator.generate(df)

            if not isinstance(result, list):
                return [], [{
                    "type": "invalid_kpi_result",
                    "message": (
                        "KPIGenerator không trả về danh sách KPI hợp lệ."
                    ),
                }]

            return result, []

        except Exception as error:
            print("KPI generation failed:", str(error))

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
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        try:
            result = self.chart_generator.generate(df)

            if not isinstance(result, list):
                return [], [{
                    "type": "invalid_chart_result",
                    "message": (
                        "ChartGenerator không trả về danh sách biểu đồ hợp lệ."
                    ),
                }]

            return result, []

        except Exception as error:
            print("Chart generation failed:", str(error))

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
        warnings: list[dict[str, str]],
    ) -> str:
        if kpis and charts and not warnings:
            return "complete"

        if kpis or charts:
            return "partial"

        return "insufficient_data"