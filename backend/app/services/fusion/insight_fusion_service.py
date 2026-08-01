from typing import Any

import pandas as pd

from app.services.fusion.fusion_models import (
    FusionResponse,
    FusionSource,
)
from app.services.fusion.knowledge_query_builder import (
    KnowledgeQueryBuilder,
)


class InsightFusionService:
    """
    Kết hợp:

    1. Insight được phát hiện từ dữ liệu bảng.
    2. Tri thức được truy xuất từ hệ thống RAG.
    3. Khuyến nghị hỗ trợ ra quyết định.
    """

    def __init__(
        self,
        insight_engine: Any,
        knowledge_service: Any,
    ) -> None:
        self.insight_engine = insight_engine
        self.knowledge_service = knowledge_service
        self.query_builder = KnowledgeQueryBuilder()


    def _infer_category(
        self,
        df: pd.DataFrame,
        requested_category: str | None = None,
    ) -> str:
        """
        Tự nhận diện nhóm tri thức phù hợp
        dựa trên tên cột của dataset.
        """

        allowed_categories = {
            "hoc_vu",
            "tot_nghiep",
            "hoc_bong",
            "dao_tao",
        }

        if requested_category:
            normalized_requested = (
                requested_category
                .strip()
                .lower()
            )

            if normalized_requested in allowed_categories:
                return normalized_requested

        normalized_columns = {
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            for column in df.columns
        }

        graduation_keywords = {
            "graduation_status",
            "graduation_classification",
            "graduation_eligibility",
            "graduation_result",
            "eligible_for_graduation",
            "mandatory_courses_remaining",
            "required_courses_remaining",
            "credits_completed",
            "credits_required",
            "total_credits",
            "cpa",
        }

        scholarship_keywords = {
            "scholarship_status",
            "scholarship_type",
            "scholarship_amount",
            "financial_aid",
        }

        academic_warning_keywords = {
            "academic_warning",
            "warning_level",
            "academic_risk",
            "risk_level",
            "failed_credits",
            "failed_courses",
            "semester_gpa",
        }

        training_keywords = {
            "course",
            "subject",
            "semester",
            "credits_registered",
            "credits_passed",
            "class",
            "major",
        }

        graduation_score = len(
            normalized_columns & graduation_keywords
        )

        scholarship_score = len(
            normalized_columns & scholarship_keywords
        )

        warning_score = len(
            normalized_columns & academic_warning_keywords
        )

        training_score = len(
            normalized_columns & training_keywords
        )

        scores = {
            "tot_nghiep": graduation_score,
            "hoc_bong": scholarship_score,
            "hoc_vu": warning_score,
            "dao_tao": training_score,
        }

        best_category = max(
            scores,
            key=scores.get,
        )

        if scores[best_category] > 0:
            return best_category

        return "dao_tao"

    def generate(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        category: str | None = None,
    ) -> FusionResponse:
        """
        Tạo kết quả Insight + RAG Fusion.
        """

        resolved_category = self._infer_category(
            df=df,
            requested_category=category,
        )

        print(
            "[InsightFusion] Resolved category:",
            resolved_category,
        )

        insight_result = self.insight_engine.generate(
            df=df,
            dataset_name=dataset_name,
        )

        findings = self._extract_findings(
            insight_result
        )

        knowledge_query = self.query_builder.build(
            findings=findings,
            dataset_name=dataset_name,
            category=resolved_category,
            insight_result=insight_result,
        )

        knowledge_result = self._ask_knowledge_service(
            query=knowledge_query,
            category=resolved_category,
        )

        knowledge_answer = self._extract_answer(
            knowledge_result
        )

        sources = self._extract_sources(
            knowledge_result
        )

        generation_mode = (
            self._extract_generation_mode(
                knowledge_result
            )
        )

        recommendations = self._build_recommendations(
            findings=findings,
            knowledge_answer=knowledge_answer,
            category=resolved_category,
        )

        return FusionResponse(
            dataset_name=dataset_name,
            data_findings=findings,
            knowledge_query=knowledge_query,
            knowledge_answer=knowledge_answer,
            recommendations=recommendations,
            sources=sources,
            metadata={
                "category": resolved_category,
                "row_count": len(df),
                "column_count": len(df.columns),
                "generation_mode": generation_mode,
                "has_knowledge_answer": bool(
                    knowledge_answer.strip()
                ),
                "source_count": len(sources),
            },
        )

    def _ask_knowledge_service(
        self,
        query: str,
        category: str | None,
    ) -> Any:
        """
        Gửi câu hỏi sang Knowledge Service
        và giữ đúng category đã xác định.

        Không tự động truy xuất toàn bộ kho tri thức
        để tránh lấy nhầm tài liệu khác miền nghiệp vụ.
        """

        return self.knowledge_service.ask(
            question=query,
            category=category,
        )


   
    def _extract_findings(
        self,
        insight_result: Any,
    ) -> list[str]:
        findings: list[str] = []

        if insight_result is None:
            return findings

        if isinstance(insight_result, dict):
            raw_findings = (
                insight_result.get("insights")
                or insight_result.get("findings")
                or insight_result.get("key_findings")
                or []
            )
        else:
            raw_findings = (
                getattr(
                    insight_result,
                    "insights",
                    None,
                )
                or getattr(
                    insight_result,
                    "findings",
                    None,
                )
                or getattr(
                    insight_result,
                    "key_findings",
                    None,
                )
                or []
            )

        for item in raw_findings:
            if isinstance(item, str):
                findings.append(item)
                continue

            if isinstance(item, dict):
                message = (
                    item.get("message")
                    or item.get("description")
                    or item.get("title")
                    or item.get("summary")
                )

                if message:
                    findings.append(
                        str(message)
                    )

                continue

            message = (
                getattr(
                    item,
                    "message",
                    None,
                )
                or getattr(
                    item,
                    "description",
                    None,
                )
                or getattr(
                    item,
                    "title",
                    None,
                )
                or getattr(
                    item,
                    "summary",
                    None,
                )
            )

            if message:
                findings.append(
                    str(message)
                )

        return findings[:10]

    def _extract_answer(
        self,
        knowledge_result: Any,
    ) -> str:
        if knowledge_result is None:
            return ""

        if isinstance(
            knowledge_result,
            str,
        ):
            return knowledge_result

        if isinstance(
            knowledge_result,
            dict,
        ):
            answer = (
                knowledge_result.get("answer")
                or knowledge_result.get("response")
                or knowledge_result.get("content")
                or ""
            )

            return str(answer)

        answer = (
            getattr(
                knowledge_result,
                "answer",
                None,
            )
            or getattr(
                knowledge_result,
                "response",
                None,
            )
            or getattr(
                knowledge_result,
                "content",
                None,
            )
            or ""
        )

        return str(answer)

    def _extract_sources(
        self,
        knowledge_result: Any,
    ) -> list[FusionSource]:
        if knowledge_result is None:
            return []

        if isinstance(
            knowledge_result,
            dict,
        ):
            raw_sources = (
                knowledge_result.get(
                    "sources",
                    [],
                )
                or []
            )
        else:
            raw_sources = (
                getattr(
                    knowledge_result,
                    "sources",
                    [],
                )
                or []
            )

        sources: list[FusionSource] = []

        for item in raw_sources:
            if isinstance(item, str):
                sources.append(
                    FusionSource(
                        document=item,
                    )
                )
                continue

            if isinstance(item, dict):
                document = (
                    item.get("document")
                    or item.get("source")
                    or item.get("filename")
                    or "Không xác định"
                )

                sources.append(
                    FusionSource(
                        document=str(document),
                        page=item.get("page"),
                        category=item.get("category"),
                    )
                )

                continue

            document = (
                getattr(
                    item,
                    "document",
                    None,
                )
                or getattr(
                    item,
                    "source",
                    None,
                )
                or getattr(
                    item,
                    "filename",
                    None,
                )
                or "Không xác định"
            )

            sources.append(
                FusionSource(
                    document=str(document),
                    page=getattr(
                        item,
                        "page",
                        None,
                    ),
                    category=getattr(
                        item,
                        "category",
                        None,
                    ),
                )
            )

        return sources

    def _extract_generation_mode(
        self,
        knowledge_result: Any,
    ) -> str | None:
        """
        Lấy chế độ sinh câu trả lời:

        - gemini
        - retrieval_fallback
        - hoặc giá trị khác do RAG trả về
        """

        if knowledge_result is None:
            return None

        if isinstance(
            knowledge_result,
            dict,
        ):
            metadata = (
                knowledge_result.get(
                    "metadata",
                    {},
                )
                or {}
            )

            if isinstance(metadata, dict):
                generation_mode = (
                    metadata.get(
                        "generation_mode"
                    )
                )

                if generation_mode is not None:
                    return str(
                        generation_mode
                    )

            return None

        metadata = getattr(
            knowledge_result,
            "metadata",
            None,
        )

        if isinstance(metadata, dict):
            generation_mode = metadata.get(
                "generation_mode"
            )

            if generation_mode is not None:
                return str(
                    generation_mode
                )

        return None

    def _build_recommendations(
        self,
        findings: list[str],
        knowledge_answer: str,
        category: str | None,
    ) -> list[str]:
        """
        Tạo khuyến nghị rule-based trong trường hợp
        Gemini chưa khả dụng.

        Khi RAG có câu trả lời, khuyến nghị vẫn dựa trên
        category để đảm bảo kết quả ổn định.
        """

        recommendations: list[str] = []

        normalized_category = (
            category.strip().lower()
            if category
            else None
        )

        if normalized_category == "tot_nghiep":
            recommendations.extend(
                [
                    (
                        "Rà soát số tín chỉ tích lũy của "
                        "từng sinh viên có nguy cơ."
                    ),
                    (
                        "Kiểm tra tình trạng hoàn thành "
                        "các học phần bắt buộc."
                    ),
                    (
                        "Kiểm tra chuẩn đầu ra ngoại ngữ, "
                        "tin học và các điều kiện liên quan."
                    ),
                    (
                        "Gửi cảnh báo sớm và lập kế hoạch "
                        "học tập bổ sung cho sinh viên."
                    ),
                ]
            )

        elif normalized_category == "hoc_vu":
            recommendations.extend(
                [
                    (
                        "Xác định nhóm sinh viên có GPA, "
                        "tín chỉ không đạt hoặc tiến độ học "
                        "tập thuộc diện cảnh báo."
                    ),
                    (
                        "Đối chiếu từng trường hợp với "
                        "quy chế cảnh báo học vụ trong "
                        "tài liệu chính thức."
                    ),
                    (
                        "Tổ chức tư vấn học tập và lập "
                        "kế hoạch cải thiện cho nhóm có "
                        "kết quả chưa đạt yêu cầu."
                    ),
                    (
                        "Theo dõi kết quả học tập trong "
                        "học kỳ tiếp theo để đánh giá mức "
                        "độ cải thiện."
                    ),
                ]
            )

        elif normalized_category == "hoc_bong":
            recommendations.extend(
                [
                    (
                        "Đối chiếu kết quả học tập với "
                        "tiêu chí xét học bổng."
                    ),
                    (
                        "Kiểm tra điểm rèn luyện và các "
                        "điều kiện bổ sung."
                    ),
                    (
                        "Rà soát các trường hợp đủ điều "
                        "kiện trước khi công bố danh sách."
                    ),
                ]
            )

        elif normalized_category == "dao_tao":
            recommendations.extend(
                [
                    (
                        "Rà soát tiến độ tích lũy tín chỉ "
                        "của từng nhóm sinh viên."
                    ),
                    (
                        "Kiểm tra tình trạng đăng ký học "
                        "phần, học lại và học cải thiện."
                    ),
                    (
                        "Đối chiếu các trường hợp bất thường "
                        "với quy chế đào tạo hiện hành."
                    ),
                ]
            )

        else:
            recommendations.extend(
                [
                    (
                        "Rà soát các đối tượng có dấu hiệu "
                        "bất thường trong dữ liệu."
                    ),
                    (
                        "Đối chiếu từng trường hợp với "
                        "quy định trong tài liệu chính thức."
                    ),
                    (
                        "Thiết lập cơ chế cảnh báo và "
                        "theo dõi tiến độ xử lý."
                    ),
                ]
            )

        if (
            not knowledge_answer.strip()
            and findings
        ):
            recommendations.append(
                (
                    "Bổ sung hoặc lập chỉ mục lại tài liệu "
                    "trong kho tri thức để tăng khả năng "
                    "truy xuất quy định phù hợp."
                )
            )

        return recommendations