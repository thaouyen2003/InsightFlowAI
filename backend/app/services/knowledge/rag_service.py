import os
import random
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError, ServerError

from app.services.knowledge.knowledge_service import (
    KnowledgeService,
)
from app.services.knowledge.prompt_builder import (
    KnowledgePromptBuilder,
)


BASE_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class KnowledgeRAGService:
    """
    Hệ thống Retrieval-Augmented Generation.

    Quy trình:
    1. Nhận câu hỏi
    2. Truy xuất tri thức từ ChromaDB
    3. Xây dựng prompt có ngữ cảnh
    4. Gọi Gemini
    5. Retry nếu model tạm thời quá tải
    6. Chuyển sang model dự phòng nếu cần
    7. Trả về câu trả lời và nguồn bằng chứng
    """

    DEFAULT_MODEL = "gemini-3.5-flash"
    DEFAULT_FALLBACK_MODEL = "gemini-3.1-flash-lite"

    MAX_RETRIES = 3
    BASE_RETRY_DELAY_SECONDS = 1.5

    def __init__(
        self,
        knowledge_service: KnowledgeService | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
    ) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "Không tìm thấy GEMINI_API_KEY "
                "trong file .env"
            )

        self.model = (
            model
            or os.getenv("GEMINI_MODEL")
            or self.DEFAULT_MODEL
        )

        self.fallback_model = (
            fallback_model
            or os.getenv("GEMINI_FALLBACK_MODEL")
            or self.DEFAULT_FALLBACK_MODEL
        )

        self.client = genai.Client(
            api_key=api_key
        )

        self.knowledge_service = (
            knowledge_service
            or KnowledgeService()
        )

        self.prompt_builder = (
            KnowledgePromptBuilder()
        )

    def answer(
        self,
        query: str,
        limit: int = 4,
    ) -> dict[str, Any]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "Câu hỏi không được để trống"
            )

        if limit <= 0:
            raise ValueError(
                "limit phải lớn hơn 0"
            )

        search_response = (
            self.knowledge_service.search(
                query=cleaned_query,
                limit=limit,
            )
        )

        knowledge_results = search_response[
            "results"
        ]

        if not knowledge_results:
            return {
                "query": cleaned_query,
                "answer": (
                    "Knowledge Base hiện chưa có "
                    "đủ tri thức để trả lời câu hỏi này."
                ),
                "model": None,
                "retrieved_count": 0,
                "sources": [],
                "used_fallback": False,
            }

        prompt = self.prompt_builder.build(
            query=cleaned_query,
            knowledge_results=knowledge_results,
        )

        generation_result = (
            self._generate_with_fallback(
                prompt=prompt
            )
        )

        sources = self._build_sources(
            knowledge_results
        )

        return {
            "query": cleaned_query,
            "answer": generation_result[
                "answer"
            ],
            "model": generation_result[
                "model"
            ],
            "retrieved_count": len(
                knowledge_results
            ),
            "sources": sources,
            "used_fallback": generation_result[
                "used_fallback"
            ],
        }

    def _generate_with_fallback(
        self,
        prompt: str,
    ) -> dict[str, Any]:
        """
        Gọi model chính trước.

        Nếu model chính gặp lỗi tạm thời 503:
        - Thử lại bằng exponential backoff
        - Sau đó chuyển sang model dự phòng
        """

        models_to_try = [self.model]

        if (
            self.fallback_model
            and self.fallback_model != self.model
        ):
            models_to_try.append(
                self.fallback_model
            )

        last_error: Exception | None = None

        for model_index, model_name in enumerate(
            models_to_try
        ):
            used_fallback = model_index > 0

            try:
                answer = self._generate_with_retry(
                    model_name=model_name,
                    prompt=prompt,
                )

                return {
                    "answer": answer,
                    "model": model_name,
                    "used_fallback": used_fallback,
                }

            except Exception as error:
                last_error = error

        error_message = (
            str(last_error)
            if last_error
            else "Không xác định được lỗi Gemini"
        )

        raise RuntimeError(
            "Không thể tạo câu trả lời bằng "
            "model chính hoặc model dự phòng. "
            f"Chi tiết: {error_message}"
        ) from last_error

    def _generate_with_retry(
        self,
        model_name: str,
        prompt: str,
    ) -> str:
        """
        Retry với thời gian chờ tăng dần:

        lần 1: khoảng 1.5 giây
        lần 2: khoảng 3 giây
        lần 3: khoảng 6 giây
        """

        last_error: Exception | None = None

        for attempt in range(
            1,
            self.MAX_RETRIES + 1,
        ):
            try:
                response = (
                    self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                )

                answer_text = (
                    response.text or ""
                ).strip()

                if not answer_text:
                    raise RuntimeError(
                        "Gemini không trả về nội dung"
                    )

                return answer_text

            except ServerError as error:
                last_error = error

                status_code = getattr(
                    error,
                    "status_code",
                    None,
                )

                if (
                    status_code != 503
                    or attempt >= self.MAX_RETRIES
                ):
                    raise

                delay = (
                    self.BASE_RETRY_DELAY_SECONDS
                    * (2 ** (attempt - 1))
                )

                jitter = random.uniform(
                    0,
                    0.5,
                )

                time.sleep(delay + jitter)

            except APIError as error:
                last_error = error

                status_code = getattr(
                    error,
                    "status_code",
                    None,
                )

                retryable_codes = {
                    429,
                    500,
                    502,
                    503,
                    504,
                }

                if (
                    status_code not in retryable_codes
                    or attempt >= self.MAX_RETRIES
                ):
                    raise

                delay = (
                    self.BASE_RETRY_DELAY_SECONDS
                    * (2 ** (attempt - 1))
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini không phản hồi sau "
            f"{self.MAX_RETRIES} lần thử"
        ) from last_error

    def _build_sources(
        self,
        knowledge_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        seen_sources: set[tuple[str, Any]] = set()

        for result in knowledge_results:
            metadata = result.get(
                "metadata",
                {},
            )

            if not isinstance(metadata, dict):
                metadata = {}

            filename = str(
                metadata.get(
                    "filename",
                    "Không rõ nguồn",
                )
            )

            chunk_number = metadata.get(
                "chunk_number"
            )

            source_key = (
                filename,
                chunk_number,
            )

            if source_key in seen_sources:
                continue

            seen_sources.add(source_key)

            sources.append(
                {
                    "filename": filename,
                    "chunk_number": chunk_number,
                    "source": metadata.get(
                        "source",
                        filename,
                    ),
                    "distance": result.get(
                        "distance"
                    ),
                    "excerpt": str(
                        result.get(
                            "content",
                            "",
                        )
                    )[:300],
                }
            )

        return sources