import os

from dotenv import load_dotenv
from google import genai


class EmbeddingService:
    """
    Sinh vector embedding bằng Gemini.

    Dùng task type khác nhau cho:
    - Tài liệu được lưu
    - Câu hỏi truy vấn
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

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Sinh embedding cho các chunk tài liệu.
        """

        if not texts:
            return []

        embeddings: list[list[float]] = []

        for text in texts:
            clean_text = text.strip()

            if not clean_text:
                embeddings.append([])
                continue

            response = self.client.models.embed_content(
                model=self.model,
                contents=clean_text,
                config={
                    "task_type": "RETRIEVAL_DOCUMENT",
                },
            )

            embeddings.append(
                list(response.embeddings[0].values)
            )

        return embeddings

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

        response = self.client.models.embed_content(
            model=self.model,
            contents=clean_query,
            config={
                "task_type": "RETRIEVAL_QUERY",
            },
        )

        return list(
            response.embeddings[0].values
        )