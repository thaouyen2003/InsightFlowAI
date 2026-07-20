import traceback
from typing import Any

from fastapi import HTTPException
import pandas as pd

from app.services.dashboard.chart_generator import ChartGenerator
from app.services.dashboard.data_cleaner import DataCleaner
from app.services.dashboard.data_context_builder import DataContextBuilder
from app.services.dashboard.dataset_classifier import DatasetClassifier
from app.services.dashboard.kpi_generator import KPIGenerator
from app.services.dashboard.insight_generator import InsightGenerator
from app.services.dashboard.dashboard_composer import DashboardComposer
from app.services.dashboard.llm_insight_writer import (
    LLMInsightWriter,
)

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
        self.insight_generator = InsightGenerator()
        self.dashboard_composer = DashboardComposer()
        self.llm_insight_writer = LLMInsightWriter()


    
    def generate(
        self,
        df: pd.DataFrame,
    ) -> dict[str, Any]:
        # 1. Phân tích dữ liệu ban đầu
        initial_context = self.data_context_builder.build(df)

        # 2. Làm sạch dữ liệu
        cleaned_df, cleaning_warnings = self.data_cleaner.clean(
            df=df,
            columns_metadata=initial_context["columns"],
        )

        # 3. Phân tích lại dữ liệu sau khi làm sạch
        data_context = self.data_context_builder.build(
            cleaned_df
        )

        # 4. Phân loại dataset
        dataset_profile = self.dataset_classifier.classify(
            data_context
        )

        # 5. Sinh KPI thô
        kpis, kpi_warnings = self._safe_generate_kpis(
            df=cleaned_df,
            data_context=data_context,
            dataset_profile=dataset_profile,
        )

        # 6. Sinh chart thô
        charts, chart_warnings = self._safe_generate_charts(
            df=cleaned_df,
            data_context=data_context,
            dataset_profile=dataset_profile,
        )

        # 7. Chọn lọc KPI và chart
        composed_dashboard = self.dashboard_composer.compose(
            kpis=kpis,
            charts=charts,
            data_context=data_context,
            dataset_profile=dataset_profile,
        )

        selected_kpis = composed_dashboard["kpis"]
        selected_charts = composed_dashboard["charts"]

        # 8. Gộp warnings
        warnings = [
            *data_context.get("warnings", []),
            *cleaning_warnings,
            *kpi_warnings,
            *chart_warnings,
        ]

        # 9. Sinh insight và recommendation
        insight_result = self.insight_generator.generate(
            df=cleaned_df,
            kpis=selected_kpis,
            charts=selected_charts,
            data_context=data_context,
            dataset_profile=dataset_profile,
            warnings=warnings,
        )

        # 10. Dùng LLM viết lại insight
        dashboard_summary = {
            "rows": int(len(cleaned_df)),
            "columns": int(len(cleaned_df.columns)),
        }

        llm_insight_result = (
            self.llm_insight_writer.write(
                insight_result=insight_result,
                dataset_profile=dataset_profile,
                dashboard_summary=dashboard_summary,
                warnings=warnings,
            )
        )

        # 10. Xác định trạng thái
        status = self._determine_status(
            kpis=selected_kpis,
            charts=selected_charts,
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
            "kpis": selected_kpis,
            "charts": selected_charts,
            "layout": composed_dashboard["layout"],
            "composition_summary": (
                composed_dashboard[
                    "composition_summary"
                ]
            ),
            "insights": insight_result["insights"],
            "recommendations": (
                insight_result["recommendations"]
            ),
            "insight_summary": insight_result["summary"],
            "llm_insight": llm_insight_result,
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
                print("\n===== KPI GENERATION ERROR =====")
                traceback.print_exc()
                print("================================\n")

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
        data_context: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, str]],
    ]:
        try:
            result = self.chart_generator.generate(
                df=df,
                data_context=data_context,
                dataset_profile=dataset_profile,
            )

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
    

