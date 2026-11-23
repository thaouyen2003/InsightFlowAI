import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors


class EmbeddingService:
    """
    Sinh vector embedding bằng Gemini.

    Dùng task type khác nhau cho:
    - Tài liệu được lưu
    - Câu hỏi truy vấn

    Có hỗ trợ:
    - batch embedding cho document chunks
    - retry khi gặp rate limit / quota tạm thời
    """

    def __init__(self) -> None:
        load_dotenv()

        self.api_key = os.getenv(
            "GEMINI_API_KEY",
            "",
        ).strip()

        self.model = os.getenv(
            "GEMINI_EMBEDDING_MODEL",
            "gemini-embedding-001",
        ).strip()

        if not self.api_key:
            raise ValueError(
                "Thiếu GEMINI_API_KEY trong file .env."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

        # Retry configuration
        self.max_retries = 5
        self.retry_delay_seconds = 65

    # =========================================================
    # RETRY HELPER
    # =========================================================

    def _embed_with_retry(
        self,
        contents,
        task_type: str,
    ):
        """
        Gọi Gemini embedding API với retry
        khi gặp HTTP 429 RESOURCE_EXHAUSTED.
        """

        last_error: Exception | None = None

        for attempt in range(
            1,
            self.max_retries + 1,
        ):
            try:
                return (
                    self.client.models.embed_content(
                        model=self.model,
                        contents=contents,
                        config={
                            "task_type":
                                task_type,
                        },
                    )
                )

            except errors.ClientError as error:
                last_error = error

                status_code = getattr(
                    error,
                    "status_code",
                    None,
                )

                if status_code != 429:
                    raise

                if attempt >= self.max_retries:
                    break

                wait_seconds = (
                    self.retry_delay_seconds
                    * attempt
                )

                print(
                    "\n[EMBEDDING RATE LIMIT]"
                )

                print(
                    f"Attempt "
                    f"{attempt}/"
                    f"{self.max_retries}"
                )

                print(
                    "Gemini quota tạm thời "
                    "đã đạt giới hạn."
                )

                print(
                    f"Waiting "
                    f"{wait_seconds}s "
                    "before retry..."
                )

                time.sleep(
                    wait_seconds
                )

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "Embedding request thất bại."
        )

    # =========================================================
    # DOCUMENT EMBEDDINGS
    # =========================================================

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Sinh embedding cho một batch document chunks.

        Toàn bộ các text hợp lệ trong batch được gửi
        trong một Gemini API request thay vì một
        request cho từng chunk.
        """

        if not texts:
            return []

        # Kết quả cần giữ đúng index với input.
        embeddings: list[list[float]] = [
            []
            for _ in texts
        ]

        valid_indices: list[int] = []
        valid_texts: list[str] = []

        for index, text in enumerate(
            texts
        ):
            clean_text = str(
                text or ""
            ).strip()

            if not clean_text:
                continue

            valid_indices.append(
                index
            )

            valid_texts.append(
                clean_text
            )

        if not valid_texts:
            return embeddings

        response = (
            self._embed_with_retry(
                contents=valid_texts,
                task_type=(
                    "RETRIEVAL_DOCUMENT"
                ),
            )
        )

        response_embeddings = (
            response.embeddings
            or []
        )

        if (
            len(response_embeddings)
            != len(valid_texts)
        ):
            raise RuntimeError(
                "Số embedding Gemini trả về "
                "không khớp với số document "
                "trong batch. "
                f"Expected={len(valid_texts)}, "
                f"received="
                f"{len(response_embeddings)}."
            )

        for index, embedding in zip(
            valid_indices,
            response_embeddings,
            strict=True,
        ):
            embeddings[index] = list(
                embedding.values
            )

        return embeddings

    # =========================================================
    # QUERY EMBEDDING
    # =========================================================

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        """
        Sinh embedding cho câu hỏi người dùng.
        """

        clean_query = query.strip()

        if not clean_query:
            raise ValueError(
                "Câu hỏi không được để trống."
            )

        response = (
            self._embed_with_retry(
                contents=clean_query,
                task_type=(
                    "RETRIEVAL_QUERY"
                ),
            )
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini không trả về "
                "query embedding."
            )

        return list(
            response.embeddings[0].values
        )