from __future__ import annotations

from pathlib import Path

from app.services.graduation.rule_extractor import (
    GraduationRuleExtractor,
)
from app.services.graduation.rule_repository import (
    GraduationRuleRepository,
)
from app.services.graduation.rules import (
    GraduationRuleSet,
)
from app.services.llm.llm_manager import (
    LLMManager,
)
from app.services.rag.rag_service import (
    RAGService,
)


class GraduationRuleGenerationService:
    """
    Sinh bộ luật xét tốt nghiệp từ kho tri thức PDF.

    Luồng xử lý:

    1. RAG truy xuất chunk trong category tot_nghiep.
    2. GraduationRuleExtractor xây dựng prompt.
    3. LLMManager gọi Gemini.
    4. Nếu Gemini lỗi, LLMManager gọi OpenRouter.
    5. Nội dung JSON được kiểm tra bằng Pydantic.
    6. Bộ luật hợp lệ được lưu vào database.
    """

    DEFAULT_QUERY = """
    Truy xuất đầy đủ các quy định và điều kiện để
    sinh viên được xét, công nhận và cấp bằng tốt nghiệp.

    Cần tìm chính xác các nội dung sau nếu tài liệu
    có đề cập:

    1. Điểm trung bình tích lũy tối thiểu.
    2. Số tín chỉ phải tích lũy.
    3. Điều kiện về học phần chưa đạt hoặc còn nợ.
    4. Chuẩn đầu ra ngoại ngữ.
    5. Chuẩn đầu ra tin học.
    6. Giáo dục thể chất.
    7. Giáo dục quốc phòng và an ninh.
    8. Nghĩa vụ học phí và tài chính.
    9. Điểm rèn luyện.
    10. Tình trạng kỷ luật.
    11. Khóa luận hoặc đồ án tốt nghiệp.
    12. Điều kiện riêng theo ngành, khóa hoặc
        chương trình đào tạo.
    13. Các điều kiện khác liên quan trực tiếp đến
        việc xét và công nhận tốt nghiệp.

    Chỉ truy xuất tri thức có trong tài liệu.
    Không tự suy diễn ngưỡng hoặc điều kiện.
    """.strip()

    SYSTEM_PROMPT = """
    Bạn là thành phần trích xuất tri thức có cấu trúc
    của hệ thống InsightFlowAI.

    Bạn phải dựa hoàn toàn vào nội dung tài liệu được
    cung cấp.

    Không tự đặt thêm điều kiện, ngưỡng điểm, số tín chỉ
    hoặc quy định không xuất hiện trong tài liệu.

    Kết quả phải là JSON hợp lệ và không được đặt trong
    Markdown code block.
    """.strip()

    def __init__(
        self,
        *,
        rag_service: RAGService | None = None,
        llm_manager: LLMManager | None = None,
        repository: (
            GraduationRuleRepository | None
        ) = None,
    ) -> None:
        self.rag_service = (
            rag_service
            if rag_service is not None
            else RAGService()
        )

        self.llm_manager = (
            llm_manager
            if llm_manager is not None
            else LLMManager()
        )

        self.repository = (
            repository
            if repository is not None
            else GraduationRuleRepository()
        )

        self.last_provider: str | None = None
        self.last_model: str | None = None
        self.last_llm_metadata: dict | None = None

        self.extractor = GraduationRuleExtractor(
            generate_text=self._generate_text
        )

    def _generate_text(
        self,
        prompt: str,
    ) -> str:
        """
        Sinh nội dung bằng Multi-LLM.

        Thứ tự do LLMManager quản lý:

        1. Gemini
        2. OpenRouter

        Hàm này chuyển LLMResult thành chuỗi để tương
        thích với GraduationRuleExtractor.
        """

        clean_prompt = prompt.strip()

        if not clean_prompt:
            raise ValueError(
                "Prompt trích xuất luật "
                "không được để trống."
            )

        result = self.llm_manager.generate(
            prompt=clean_prompt,
            system_prompt=self.SYSTEM_PROMPT,

            # Chưa truyền response_schema tại đây.
            # GraduationRuleExtractor sẽ tự parse JSON
            # và kiểm tra bằng GraduationRuleSet.
            response_schema=None,
        )

        if (
            not result.success
            or not result.content
            or not result.content.strip()
        ):
            raise RuntimeError(
                "Không thể trích xuất bộ luật bằng "
                "các LLM provider hiện có. "
                f"Chi tiết: "
                f"{result.error or 'Không có nội dung.'}"
            )

        self.last_provider = result.provider
        self.last_model = result.model
        self.last_llm_metadata = (
            result.metadata or {}
        )

        print(
            "[GraduationRuleGeneration] "
            f"Provider thành công: {result.provider}"
        )

        print(
            "[GraduationRuleGeneration] "
            f"Model: {result.model}"
        )

        return result.content.strip()

    def generate(
        self,
        *,
        major: str | None = None,
        cohort: str | None = None,
        query: str | None = None,
        top_k: int = 8,
    ) -> tuple[
        GraduationRuleSet,
        Path,
    ]:
        """
        Sinh bộ luật từ Knowledge Base và lưu JSON.

        Trả về:
        - GraduationRuleSet
        - Đường dẫn file JSON đã lưu
        """

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        knowledge_query = (
            query.strip()
            if query and query.strip()
            else self.DEFAULT_QUERY
        )

        retrieved_chunks = (
            self.rag_service.retrieve_chunks(
                question=knowledge_query,
                category="tot_nghiep",
                top_k=top_k,
                allow_category_fallback=False,
            )
        )

        if not retrieved_chunks:
            raise ValueError(
                "Không tìm thấy chunk thuộc category "
                "'tot_nghiep'. Hãy kiểm tra các PDF "
                "đã được index vào ChromaDB hay chưa."
            )

        valid_chunks = [
            chunk
            for chunk in retrieved_chunks
            if str(
                chunk.get(
                    "content",
                    "",
                )
            ).strip()
        ]

        print(
            "\n========== RETRIEVED CHUNKS ==========\n"
        )

        for i, chunk in enumerate(
            valid_chunks,
            start=1,
        ):
            print("=" * 80)
            print(f"Chunk {i}")

            print(
                "Document:",
                chunk.get("document_name"),
            )

            print(
                "Page:",
                chunk.get("page_number"),
            )

            print(
                "Chunk ID:",
                chunk.get("chunk_id"),
            )

            print("\nContent:")

            print(
                str(
                    chunk.get(
                        "content",
                        "",
                    )
                )[:1000]
            )

            print()




        
        if not valid_chunks:
            raise ValueError(
                "Retriever có trả kết quả nhưng "
                "nội dung các chunk đang rỗng."
            )

        try:
            rule_set = self.extractor.extract(
                retrieved_chunks=valid_chunks,
                major=major,
                cohort=cohort,
            )
        except Exception as error:
            raise RuntimeError(
                "Không thể tạo bộ luật xét tốt nghiệp "
                "từ nội dung PDF. "
                f"Provider cuối: "
                f"{self.last_provider or 'none'}. "
                f"Chi tiết: {error}"
            ) from error

        # Ghi lại provider đã thực sự sinh bộ luật.
        rule_set.generated_by = (
            f"rag_rule_extractor:"
            f"{self.last_provider or 'unknown'}"
        )

        rule_set.extraction_notes.append(
            "Bộ luật được sinh bởi provider: "
            f"{self.last_provider or 'unknown'}, "
            f"model: {self.last_model or 'unknown'}."
        )

        output_path = self.repository.save(
            rule_set
        )

        print(
            "[GraduationRuleGeneration] "
            f"Đã lưu bộ luật tại: {output_path}"
        )

        return rule_set, output_path