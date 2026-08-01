import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pydantic import BaseModel, Field

from app.services.rag.retriever import (
    KnowledgeRetriever,
    RetrievedKnowledge,
)


class KnowledgeSource(BaseModel):
    """
    Nguồn tài liệu được sử dụng trong câu trả lời.
    """

    source: str
    page: int | None = None
    category: str | None = None
    chunk_id: str
    distance: float | None = None


class RAGAnswer(BaseModel):
    """
    Kết quả cuối cùng của hệ thống RAG.
    """

    question: str
    answer: str

    sources: list[KnowledgeSource] = Field(
        default_factory=list
    )

    retrieved_count: int = 0

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class RAGService:
    """
    Điều phối quy trình Retrieval-Augmented Generation.

    Quy trình:
    1. Nhận và kiểm tra câu hỏi.
    2. Truy xuất tri thức theo category.
    3. Nếu category không có kết quả, thử lại toàn bộ kho.
    4. Xây dựng ngữ cảnh từ tài liệu.
    5. Gửi ngữ cảnh và câu hỏi cho Gemini.
    6. Nếu Gemini lỗi, dùng Retrieval Fallback.
    7. Trả lời kèm nguồn và metadata.
    """

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
    ) -> None:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        env_path = backend_dir / ".env"

        load_dotenv(
            dotenv_path=env_path
        )

        self.api_key = os.getenv(
            "GEMINI_API_KEY",
            "",
        ).strip()

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        ).strip()

        self.max_retries = self._read_positive_int_env(
            name="GEMINI_MAX_RETRIES",
            default=3,
        )

        self.retry_delay_seconds = (
            self._read_positive_int_env(
                name="GEMINI_RETRY_DELAY_SECONDS",
                default=3,
            )
        )

        if not self.api_key:
            raise ValueError(
                "Thiếu GEMINI_API_KEY trong file "
                f"{env_path}."
            )

        if not self.model:
            raise ValueError(
                "GEMINI_MODEL không được để trống."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

        self.retriever = (
            retriever
            if retriever is not None
            else KnowledgeRetriever()
        )

    def ask(
        self,
        question: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> RAGAnswer:
        """
        Trả lời câu hỏi dựa trên Knowledge Base.

        Nếu không tìm thấy kết quả trong category được
        yêu cầu, hệ thống tự động truy xuất lại trên toàn
        bộ kho tri thức.
        """

        clean_question = question.strip()

        if not clean_question:
            raise ValueError(
                "Câu hỏi không được để trống."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        requested_category = (
            category.strip()
            if category
            else None
        )

        effective_category = requested_category
        category_fallback_used = False

        retrieved_items = self._retrieve(
            question=clean_question,
            top_k=top_k,
            category=requested_category,
        )

        # Nếu category lọc quá chặt, thử lại toàn bộ
        # Knowledge Base để tránh trả kết quả rỗng.
        if (
            not retrieved_items
            and requested_category is not None
        ):
            print(
                "NO RESULT FOR CATEGORY:",
                requested_category,
                "- RETRYING WITHOUT CATEGORY",
            )

            retrieved_items = self._retrieve(
                question=clean_question,
                top_k=top_k,
                category=None,
            )

            effective_category = None
            category_fallback_used = True

        if not retrieved_items:
            return RAGAnswer(
                question=clean_question,
                answer=(
                    "Không tìm thấy thông tin phù hợp "
                    "trong kho tri thức hiện tại."
                ),
                sources=[],
                retrieved_count=0,
                metadata={
                    "model": self.model,
                    "top_k": top_k,
                    "requested_category": (
                        requested_category
                    ),
                    "effective_category": (
                        effective_category
                    ),
                    "category_fallback_used": (
                        category_fallback_used
                    ),
                    "generation_mode": (
                        "no_retrieval_result"
                    ),
                },
            )

        context = self.retriever.build_context(
            retrieved_items
        )

        if not context.strip():
            return RAGAnswer(
                question=clean_question,
                answer=(
                    "Hệ thống đã tìm thấy tài liệu liên "
                    "quan nhưng chưa thể xây dựng ngữ cảnh "
                    "để trả lời."
                ),
                sources=self._build_sources(
                    retrieved_items
                ),
                retrieved_count=len(
                    retrieved_items
                ),
                metadata={
                    "model": self.model,
                    "top_k": top_k,
                    "requested_category": (
                        requested_category
                    ),
                    "effective_category": (
                        effective_category
                    ),
                    "category_fallback_used": (
                        category_fallback_used
                    ),
                    "generation_mode": (
                        "empty_context"
                    ),
                },
            )

        prompt = self._build_prompt(
            question=clean_question,
            context=context,
        )

        generation_mode = "gemini"
        generation_error: str | None = None

        try:
            answer_text = self._generate_answer(
                prompt=prompt,
                max_retries=self.max_retries,
            )

            if not answer_text:
                raise RuntimeError(
                    "Gemini trả về nội dung trống."
                )

        except Exception as error:
            print(
                "GEMINI UNAVAILABLE. "
                "USING RETRIEVAL FALLBACK:",
                error,
            )

            generation_mode = (
                "retrieval_fallback"
            )

            generation_error = str(error)

            answer_text = (
                self._build_fallback_answer(
                    retrieved_items=(
                        retrieved_items
                    ),
                )
            )

        return RAGAnswer(
            question=clean_question,
            answer=answer_text,
            sources=self._build_sources(
                retrieved_items
            ),
            retrieved_count=len(
                retrieved_items
            ),
            metadata={
                "model": self.model,
                "top_k": top_k,
                "requested_category": (
                    requested_category
                ),
                "effective_category": (
                    effective_category
                ),
                "category_fallback_used": (
                    category_fallback_used
                ),
                "generation_mode": (
                    generation_mode
                ),
                "generation_error": (
                    generation_error
                ),
            },
        )


    def retrieve_chunks(
        self,
        question: str,
        category: str | None = None,
        top_k: int = 10,
        *,
        allow_category_fallback: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Truy xuất các chunk tri thức ở dạng dữ liệu thô.

        Hàm này được sử dụng cho những module cần
        xử lý trực tiếp nội dung RAG, chẳng hạn:

        - Trích xuất luật xét tốt nghiệp
        - Trích xuất điều kiện học bổng
        - Trích xuất quy định học vụ

        Khác với ask(), hàm này không gọi LLM để
        tạo câu trả lời cuối cùng.
        """

        clean_question = question.strip()

        if not clean_question:
            raise ValueError(
                "Câu truy vấn không được để trống."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        requested_category = (
            category.strip()
            if category
            else None
        )

        retrieved_items = self._retrieve(
            question=clean_question,
            top_k=top_k,
            category=requested_category,
        )

        if (
            not retrieved_items
            and requested_category is not None
            and allow_category_fallback
        ):
            retrieved_items = self._retrieve(
                question=clean_question,
                top_k=top_k,
                category=None,
            )

        normalized_chunks: list[
            dict[str, Any]
        ] = []

        for index, item in enumerate(
            retrieved_items,
            start=1,
        ):
            if hasattr(item, "model_dump"):
                item_data = item.model_dump()
            elif isinstance(item, dict):
                item_data = item
            else:
                item_data = vars(item)

            document_name = (
                item_data.get("source")
                or item_data.get("document_name")
                or item_data.get("filename")
                or "unknown.pdf"
            )

            page_number = (
                item_data.get("page")
                if item_data.get("page") is not None
                else item_data.get("page_number")
            )

            chunk_id = (
                item_data.get("chunk_id")
                or item_data.get("id")
                or f"retrieved_chunk_{index}"
            )

            content = (
                item_data.get("content")
                or item_data.get("text")
                or item_data.get("document")
                or ""
            )

            item_category = (
                item_data.get("category")
                or requested_category
            )

            distance = item_data.get(
                "distance"
            )

            normalized_chunks.append(
                {
                    "document_name": str(
                        document_name
                    ),
                    "page_number": page_number,
                    "chunk_id": str(chunk_id),
                    "content": str(content),
                    "category": item_category,
                    "distance": distance,
                }
            )

        return normalized_chunks


    def generate_text(
        self,
        prompt: str,
    ) -> str:
        """
        Gọi Gemini bằng prompt tùy chỉnh.

        Hàm này cho phép các module khác sử dụng
        chung cơ chế Gemini và retry hiện tại,
        nhưng tự định nghĩa prompt riêng.
        """

        clean_prompt = prompt.strip()

        if not clean_prompt:
            raise ValueError(
                "Prompt không được để trống."
            )

        generated_text = self._generate_answer(
            prompt=clean_prompt,
            max_retries=self.max_retries,
        )

        if not generated_text:
            raise RuntimeError(
                "Gemini trả về nội dung trống."
            )

        return generated_text.strip()

    

    def _retrieve(
        self,
        question: str,
        top_k: int,
        category: str | None,
    ) -> list[RetrievedKnowledge]:
        """
        Gọi retriever và chuẩn hóa kết quả.
        """

        result = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            category=category,
        )

        return result or []

    def _generate_answer(
        self,
        prompt: str,
        max_retries: int,
    ) -> str:
        """
        Gọi Gemini và thử lại khi dịch vụ tạm quá tải.
        """

        last_error: Exception | None = None

        for attempt in range(
            1,
            max_retries + 1,
        ):
            try:
                print(
                    "GEMINI ATTEMPT:",
                    attempt,
                    "/",
                    max_retries,
                )

                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                )

                return (
                    response.text or ""
                ).strip()

            except errors.ServerError as error:
                last_error = error

                status_code = getattr(
                    error,
                    "code",
                    None,
                )

                print(
                    "GEMINI SERVER ERROR:",
                    status_code,
                    str(error),
                )

                if attempt < max_retries:
                    wait_seconds = (
                        attempt
                        * self.retry_delay_seconds
                    )

                    print(
                        "RETRY AFTER:",
                        wait_seconds,
                        "SECONDS",
                    )

                    time.sleep(
                        wait_seconds
                    )

            except Exception as error:
                raise RuntimeError(
                    "Không thể gọi Gemini: "
                    f"{error}"
                ) from error

        raise RuntimeError(
            "Gemini đang tạm thời quá tải "
            f"sau {max_retries} lần thử. "
            f"Chi tiết: {last_error}"
        )

    def _build_prompt(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        Tạo prompt chống suy diễn và yêu cầu Gemini
        trình bày câu trả lời có cấu trúc.
        """

        return f"""
Bạn là trợ lý quản lý tri thức giáo dục của
Trường Đại học Văn Hiến.

Nhiệm vụ của bạn là trả lời câu hỏi chỉ dựa trên
phần NGỮ CẢNH TÀI LIỆU được cung cấp bên dưới.

YÊU CẦU BẮT BUỘC:

1. Không bổ sung thông tin ngoài ngữ cảnh.
2. Không suy đoán khi tài liệu không nêu rõ.
3. Nếu không đủ thông tin, phải nói rõ:
   "Tài liệu hiện có chưa cung cấp đủ thông tin
   để trả lời chính xác câu hỏi này."
4. Trả lời hoàn toàn bằng tiếng Việt.
5. Trả lời trực tiếp câu hỏi trước.
6. Sau phần trả lời trực tiếp, giải thích các
   điều kiện, tiêu chí hoặc quy định liên quan.
7. Mỗi thông tin quan trọng phải ghi nguồn theo
   dạng: [Tên tài liệu, trang X].
8. Không tạo tên tài liệu hoặc số trang không
   xuất hiện trong ngữ cảnh.
9. Không sao chép toàn bộ ngữ cảnh một cách máy móc.
10. Ưu tiên diễn giải ngắn gọn, rõ ràng và có thể
    sử dụng để hỗ trợ ra quyết định.

CẤU TRÚC CÂU TRẢ LỜI:

Tóm tắt:
Nêu câu trả lời trực tiếp trong 1–3 câu.

Các quy định hoặc điều kiện liên quan:
Trình bày thành các ý rõ ràng.

Khuyến nghị xử lý:
Chỉ đưa ra khuyến nghị nếu có căn cứ trong tài liệu.

Nguồn tham khảo:
Liệt kê tên tài liệu và số trang đã sử dụng.

NGỮ CẢNH TÀI LIỆU:
--------------------
{context}
--------------------

CÂU HỎI:
{question}

CÂU TRẢ LỜI:
""".strip()

    def _build_sources(
        self,
        retrieved_items: list[
            RetrievedKnowledge
        ],
    ) -> list[KnowledgeSource]:
        """
        Chuẩn hóa và loại bỏ nguồn trùng lặp theo
        tài liệu và số trang.
        """

        sources: list[KnowledgeSource] = []

        seen_sources: set[
            tuple[str, int | None]
        ] = set()

        for item in retrieved_items:
            source_key = (
                item.source,
                item.page,
            )

            if source_key in seen_sources:
                continue

            seen_sources.add(
                source_key
            )

            sources.append(
                KnowledgeSource(
                    source=item.source,
                    page=item.page,
                    category=item.category,
                    chunk_id=item.chunk_id,
                    distance=item.distance,
                )
            )

        return sources

    def _build_fallback_answer(
        self,
        retrieved_items: list[
            RetrievedKnowledge
        ],
    ) -> str:
        """
        Tạo câu trả lời trực tiếp từ các đoạn tri thức
        khi Gemini tạm thời không khả dụng.
        """

        if not retrieved_items:
            return (
                "Hệ thống chưa tìm thấy nội dung "
                "phù hợp trong kho tri thức."
            )

        answer_parts: list[str] = []

        for index, item in enumerate(
            retrieved_items[:5],
            start=1,
        ):
            content = item.content.strip()

            if not content:
                continue

            source_label = item.source

            if item.page is not None:
                source_label += (
                    f", trang {item.page}"
                )

            answer_parts.append(
                f"{index}. {content}\n"
                f"Nguồn: [{source_label}]"
            )

        if not answer_parts:
            return (
                "Hệ thống đã tìm thấy tài liệu liên quan "
                "nhưng chưa thể trích xuất nội dung."
            )

        return (
            "Gemini hiện đang tạm thời quá tải. "
            "Hệ thống đã chuyển sang chế độ truy xuất "
            "trực tiếp từ kho tri thức.\n\n"
            + "\n\n".join(
                answer_parts
            )
            + (
                "\n\nLưu ý: Nội dung trên được trích xuất "
                "trực tiếp từ tài liệu và chưa được Gemini "
                "tổng hợp hoặc diễn giải."
            )
        )

    @staticmethod
    def _read_positive_int_env(
        name: str,
        default: int,
    ) -> int:
        """
        Đọc biến môi trường dạng số nguyên dương.
        """

        raw_value = os.getenv(
            name,
            str(default),
        ).strip()

        try:
            value = int(raw_value)
        except ValueError:
            return default

        return value if value > 0 else default