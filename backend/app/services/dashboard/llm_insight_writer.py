import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.services.dashboard.llm_insight_models import (
    LLMInsightResponse,
    LLMInsightResult,
)


class LLMInsightWriter:
    """
    Dùng Gemini để viết lại insight thống kê thành nội dung
    phân tích dễ đọc và chuyên nghiệp.

    Nguyên tắc:
    - Backend chịu trách nhiệm tính toán số liệu.
    - LLM chỉ diễn giải insight và evidence đã có.
    - Không gửi toàn bộ DataFrame lên Gemini.
    - Không để LLM tự tạo thêm số liệu.
    - Dashboard vẫn hoạt động nếu LLM bị tắt hoặc API lỗi.
    """

    MAX_INPUT_INSIGHTS = 6
    MAX_INPUT_RECOMMENDATIONS = 4
    MAX_INPUT_WARNINGS = 5

    def __init__(self) -> None:
        load_dotenv(
            dotenv_path=".env",
            override=True,
        )

        self.enabled = (
            os.getenv(
                "ENABLE_LLM_INSIGHTS",
                "false",
            ).strip().lower()
            == "true"
        )

        self.api_key = os.getenv(
            "GEMINI_API_KEY",
            "",
        ).strip()

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash",
        ).strip()

        self.client: genai.Client | None = None

        if self.enabled and self.api_key:
            self.client = genai.Client(
                api_key=self.api_key,
            )

    def write(
        self,
        insight_result: dict[str, Any],
        dataset_profile: dict[str, Any],
        dashboard_summary: dict[str, Any],
        warnings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Viết lại insight bằng Gemini.
        """

        if not self.enabled:
            return self._build_disabled_result(
                error=(
                    "LLM Insight đang bị tắt. "
                    "Đặt ENABLE_LLM_INSIGHTS=true "
                    "để kích hoạt."
                )
            )

        if not self.api_key:
            return self._build_disabled_result(
                error=(
                    "Không tìm thấy GEMINI_API_KEY "
                    "trong file .env."
                )
            )

        if self.client is None:
            return self._build_disabled_result(
                error=(
                    "Gemini client chưa được khởi tạo."
                )
            )

        insights = insight_result.get(
            "insights",
            [],
        )

        recommendations = insight_result.get(
            "recommendations",
            [],
        )

        if not insights:
            return LLMInsightResult(
                enabled=True,
                generated=False,
                model=self.model,
                executive_summary=None,
                key_findings=[],
                recommendations=[],
                error=(
                    "Không có insight định lượng "
                    "để Gemini diễn giải."
                ),
            ).model_dump()

        prompt_payload = self._build_prompt_payload(
            insights=insights,
            recommendations=recommendations,
            dataset_profile=dataset_profile,
            dashboard_summary=dashboard_summary,
            warnings=warnings or [],
        )

        try:
            parsed_response = self._request_llm(
                prompt_payload=prompt_payload,
            )

            return LLMInsightResult(
                enabled=True,
                generated=True,
                model=self.model,
                executive_summary=(
                    parsed_response.executive_summary
                ),
                key_findings=(
                    parsed_response.key_findings
                ),
                recommendations=(
                    parsed_response.recommendations
                ),
                error=None,
            ).model_dump()

       
        except Exception as error:
            error_message = str(error)

            print(
                "Gemini insight generation failed:",
                error_message,
            )
            return self._build_local_fallback(
                insights=insights,
                recommendations=recommendations,
                dashboard_summary=dashboard_summary,
                original_error=error_message,
            )

            # if (
            #     "429" in error_message
            #     or "RESOURCE_EXHAUSTED" in error_message
            #     or "Quota exceeded" in error_message
            # ):
            #     friendly_error = (
            #         "Gemini đã đạt giới hạn sử dụng hiện tại. "
            #         "Các insight và khuyến nghị được phân tích "
            #         "từ dữ liệu vẫn hoạt động bình thường."
            #     )
            # else:
            #     friendly_error = (
            #         "Không thể tạo nội dung AI Insight vào lúc này. "
            #         "Các insight và khuyến nghị từ hệ thống "
            #         "vẫn được hiển thị bình thường."
            #     )

            # return LLMInsightResult(
            #     enabled=True,
            #     generated=False,
            #     model=self.model,
            #     executive_summary=None,
            #     key_findings=[],
            #     recommendations=[],
            #     error=friendly_error,
            # ).model_dump()

    def _build_local_fallback(
        self,
        insights: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
        dashboard_summary: dict[str, Any],
        original_error: str,
    ) -> dict[str, Any]:
        """
        Tạo nội dung AI Insight từ kết quả phân tích nội bộ
        khi Gemini tạm thời không khả dụng.

        Không tạo thêm số liệu mới.
        Chỉ diễn giải lại insight và recommendation
        đã được backend tính toán.
        """

        key_findings: list[dict[str, str]] = []

        for insight in insights[
            :self.MAX_INPUT_INSIGHTS
        ]:
            title = str(
                insight.get(
                    "title",
                    "Phát hiện từ dữ liệu",
                )
            )

            description = str(
                insight.get(
                    "description",
                    "Hệ thống đã ghi nhận một đặc điểm "
                    "đáng chú ý trong dữ liệu.",
                )
            )

            insight_type = insight.get(
                "type",
                "information",
            )

            if hasattr(insight_type, "value"):
                insight_type = insight_type.value

            insight_type = str(insight_type).lower()

            severity_value = insight.get(
                "severity",
                "medium",
            )

            if hasattr(severity_value, "value"):
                severity_value = (
                    severity_value.value
                )

            severity_value = str(
                severity_value
            ).lower()

            if (
                insight_type == "positive"
            ):
                display_severity = "positive"

            elif (
                insight_type == "critical"
                or severity_value
                in {"high", "critical"}
            ):
                display_severity = "negative"

            elif (
                insight_type == "warning"
                or severity_value == "medium"
            ):
                display_severity = "warning"

            else:
                display_severity = "neutral"

            key_findings.append(
                {
                    "title": title,
                    "description": description,
                    "severity": display_severity,
                }
            )

        local_recommendations: list[
            dict[str, str]
        ] = []

        for recommendation in recommendations[
            :self.MAX_INPUT_RECOMMENDATIONS
        ]:
            title = str(
                recommendation.get(
                    "title",
                    "Khuyến nghị xử lý",
                )
            )

            description = str(
                recommendation.get(
                    "description",
                    "Cần xem xét và theo dõi "
                    "phát hiện liên quan.",
                )
            )

            priority_value = recommendation.get(
                "priority",
                "medium",
            )

            if hasattr(priority_value, "value"):
                priority_value = (
                    priority_value.value
                )

            priority_value = str(
                priority_value
            ).lower()

            if priority_value in {
                "critical",
                "high",
            }:
                display_priority = "high"
            elif priority_value == "low":
                display_priority = "low"
            else:
                display_priority = "medium"

            local_recommendations.append(
                {
                    "title": title,
                    "description": description,
                    "priority": display_priority,
                }
            )

        total_insights = len(insights)
        total_recommendations = len(
            recommendations
        )

        kpi_count = dashboard_summary.get(
            "kpi_count",
            0,
        )

        chart_count = dashboard_summary.get(
            "chart_count",
            0,
        )

        summary_parts = [
            (
                "InsightFlowAI đã hoàn thành quá trình "
                "phân tích dữ liệu bằng các bộ phát hiện "
                "nội bộ."
            ),
            (
                f"Hệ thống ghi nhận {total_insights} "
                "phát hiện dữ liệu và tạo "
                f"{total_recommendations} khuyến nghị."
            ),
        ]

        if kpi_count or chart_count:
            summary_parts.append(
                (
                    f"Dashboard hiện có {kpi_count} KPI "
                    f"và {chart_count} biểu đồ hỗ trợ "
                    "theo dõi và ra quyết định."
                )
            )

        summary_parts.append(
            (
                "Nội dung này được tổng hợp trực tiếp "
                "từ kết quả định lượng của hệ thống "
                "do Gemini đang tạm thời không khả dụng."
            )
        )

        executive_summary = " ".join(
            summary_parts
        )

        print(
            "Using local AI Insight fallback:",
            original_error,
        )

        return LLMInsightResult(
            enabled=True,
            generated=True,
            model="InsightFlowAI Engine",
            executive_summary=executive_summary,
            key_findings=key_findings,
            recommendations=local_recommendations,
            error=None,
        ).model_dump()

    def _request_llm(
        self,
        prompt_payload: dict[str, Any],
    ) -> LLMInsightResponse:
        """
        Gửi insight đã tính toán đến Gemini và yêu cầu
        đầu ra đúng schema LLMInsightResponse.
        """

        if self.client is None:
            raise RuntimeError(
                "Gemini client chưa được khởi tạo."
            )

        system_prompt = self._build_system_prompt()

        user_payload = json.dumps(
            prompt_payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        user_prompt = (
            "Hãy phân tích dữ liệu dashboard dưới đây "
            "và trả về kết quả đúng schema được yêu cầu.\n\n"
            f"{user_payload}"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=LLMInsightResponse,
            ),
        )

        if not response.text:
            raise ValueError(
                "Gemini không trả về nội dung."
            )

        return LLMInsightResponse.model_validate_json(
            response.text
        )

    def _build_system_prompt(self) -> str:
        """
        Prompt hệ thống kiểm soát cách Gemini diễn giải.
        """

        return """
Bạn là chuyên gia phân tích dữ liệu và Business Intelligence
của hệ thống InsightFlowAI.

Nhiệm vụ của bạn là viết lại các insight định lượng do backend
đã tính toán thành nội dung tiếng Việt rõ ràng, chuyên nghiệp,
ngắn gọn và hữu ích cho người ra quyết định.

QUY TẮC BẮT BUỘC:

1. Chỉ sử dụng dữ liệu được cung cấp trong đầu vào.

2. Không tự tính toán lại số liệu.

3. Không tạo thêm doanh thu, tỷ lệ, số lượng, xu hướng,
nguyên nhân hoặc kết luận không có trong evidence.

4. Không khẳng định quan hệ nhân quả nếu dữ liệu chỉ thể hiện
mối liên hệ hoặc xu hướng.

5. Nếu dữ liệu chưa đủ để kết luận, phải dùng cách diễn đạt
thận trọng như:
- "dữ liệu cho thấy"
- "có dấu hiệu"
- "cần theo dõi thêm"
- "chưa đủ cơ sở để kết luận"

6. Executive summary phải dài khoảng 2 đến 4 câu.

7. Key findings tối đa 6 mục.

8. Recommendations tối đa 4 mục.

9. Recommendation phải xuất phát trực tiếp từ insight đã có.

10. Không đề xuất hành động quá cụ thể nếu dataset không đủ
thông tin nghiệp vụ.

11. Không nhắc đến prompt, JSON, backend, mô hình ngôn ngữ
hoặc quá trình tạo nội dung.

12. Nội dung trả về phải bằng tiếng Việt.

13. Tiêu đề phải ngắn gọn, dễ đọc trên dashboard.

14. Severity:
- positive: kết quả hoặc xu hướng tích cực
- negative: kết quả hoặc xu hướng tiêu cực
- warning: cần chú ý hoặc dữ liệu có rủi ro
- neutral: thông tin mô tả, chưa thể hiện tốt hoặc xấu

15. Priority:
- high: cần ưu tiên xử lý
- medium: nên theo dõi hoặc xem xét
- low: thông tin bổ sung
""".strip()

    def _build_prompt_payload(
        self,
        insights: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
        dataset_profile: dict[str, Any],
        dashboard_summary: dict[str, Any],
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Chỉ lấy dữ liệu cần thiết để gửi đến Gemini.
        """

        safe_insights = [
            self._sanitize_insight(item)
            for item in insights[
                :self.MAX_INPUT_INSIGHTS
            ]
            if isinstance(item, dict)
        ]

        safe_recommendations = [
            self._sanitize_recommendation(item)
            for item in recommendations[
                :self.MAX_INPUT_RECOMMENDATIONS
            ]
            if isinstance(item, dict)
        ]

        safe_warnings = [
            self._sanitize_warning(item)
            for item in warnings[
                :self.MAX_INPUT_WARNINGS
            ]
            if isinstance(item, dict)
        ]

        return {
            "task": (
                "Viết executive summary, key findings "
                "và recommendations cho dashboard."
            ),
            "dataset": {
                "dataset_type": dataset_profile.get(
                    "dataset_type",
                    "generic",
                ),
                "confidence": dataset_profile.get(
                    "confidence",
                    0,
                ),
                "rows": self._safe_integer(
                    dashboard_summary.get(
                        "rows",
                        0,
                    )
                ),
                "columns": self._safe_integer(
                    dashboard_summary.get(
                        "columns",
                        0,
                    )
                ),
            },
            "calculated_insights": safe_insights,
            "rule_based_recommendations": (
                safe_recommendations
            ),
            "data_quality_warnings": safe_warnings,
            "output_requirements": {
                "language": "Vietnamese",
                "maximum_key_findings": 6,
                "maximum_recommendations": 4,
                "do_not_invent_numbers": True,
                "do_not_claim_unproven_causes": True,
            },
        }

    def _sanitize_insight(
        self,
        insight: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": str(
                insight.get(
                    "id",
                    "",
                )
            ),
            "type": str(
                insight.get(
                    "type",
                    "general",
                )
            ),
            "title": str(
                insight.get(
                    "title",
                    "",
                )
            ),
            "description": str(
                insight.get(
                    "description",
                    "",
                )
            ),
            "severity": str(
                insight.get(
                    "severity",
                    "neutral",
                )
            ),
            "priority": self._safe_integer(
                insight.get(
                    "priority",
                    0,
                )
            ),
            "evidence": self._sanitize_evidence(
                insight.get(
                    "evidence",
                    {},
                )
            ),
        }

    def _sanitize_recommendation(
        self,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": str(
                recommendation.get(
                    "id",
                    "",
                )
            ),
            "title": str(
                recommendation.get(
                    "title",
                    "",
                )
            ),
            "description": str(
                recommendation.get(
                    "description",
                    "",
                )
            ),
            "priority": str(
                recommendation.get(
                    "priority",
                    "medium",
                )
            ),
            "based_on": recommendation.get(
                "based_on"
            ),
        }

    def _sanitize_warning(
        self,
        warning: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "type": str(
                warning.get(
                    "type",
                    "data_warning",
                )
            ),
            "message": str(
                warning.get(
                    "message",
                    "",
                )
            ),
            "column": warning.get(
                "column"
            ),
        }

    def _sanitize_evidence(
        self,
        evidence: Any,
    ) -> dict[str, Any]:
        if not isinstance(evidence, dict):
            return {}

        safe_evidence: dict[str, Any] = {}

        for key, value in evidence.items():
            safe_evidence[str(key)] = (
                self._make_json_safe(value)
            )

        return safe_evidence

    def _make_json_safe(
        self,
        value: Any,
    ) -> Any:
        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        if isinstance(value, dict):
            return {
                str(key): self._make_json_safe(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                self._make_json_safe(item)
                for item in value
            ]

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass

        return str(value)

    def _safe_integer(
        self,
        value: Any,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0

    def _build_disabled_result(
        self,
        error: str,
    ) -> dict[str, Any]:
        return LLMInsightResult(
            enabled=self.enabled,
            generated=False,
            model=self.model,
            executive_summary=None,
            key_findings=[],
            recommendations=[],
            error=error,
        ).model_dump()