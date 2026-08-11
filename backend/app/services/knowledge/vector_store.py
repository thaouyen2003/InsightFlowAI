import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
)


class KnowledgeVectorStore:
    """
    Quản lý kho vector tri thức của InsightFlowAI.

    Chức năng:
    - Nhận knowledge chunks
    - Tạo embedding bằng Gemini
    - Lưu embedding vào ChromaDB
    - Tìm kiếm tri thức theo ngữ nghĩa
    """

    DEFAULT_COLLECTION_NAME = "insightflow_knowledge"
    DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"

    def __init__(
        self,
        persist_directory: str | Path = (
            "knowledge_base/vector_store"
        ),
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_model: str | None = None,
    ) -> None:
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "Không tìm thấy GEMINI_API_KEY "
                "trong file .env"
            )

        selected_model = (
            embedding_model
            or os.getenv("GEMINI_EMBEDDING_MODEL")
            or self.DEFAULT_EMBEDDING_MODEL
        )

        self.persist_directory = Path(
            persist_directory
        )

        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.collection_name = collection_name
        self.embedding_model = selected_model

        self.embeddings = (
            GoogleGenerativeAIEmbeddings(
                model=selected_model,
                google_api_key=api_key,
            )
        )

        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(
                self.persist_directory
            ),
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> int:
        """
        Thêm các knowledge chunk vào ChromaDB.

        Trả về số chunk được lưu.
        """

        if not chunks:
            return 0

        documents: list[Document] = []
        ids: list[str] = []

        for chunk in chunks:
            chunk_id = str(
                chunk.get("id", "")
            ).strip()

            text = str(
                chunk.get("text", "")
            ).strip()

            metadata = chunk.get(
                "metadata",
                {},
            )

            if not chunk_id or not text:
                continue

            if not isinstance(metadata, dict):
                metadata = {}

            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )

            ids.append(chunk_id)

        if not documents:
            return 0

        self.vector_store.add_documents(
            documents=documents,
            ids=ids,
        )

        return len(documents)

    def search(
        self,
        query: str,
        limit: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Truy vấn các đoạn tri thức gần nhất
        với câu hỏi theo semantic similarity.
        """

        cleaned_query = query.strip()

        if not cleaned_query:
            return []

        if limit <= 0:
            raise ValueError(
                "limit phải lớn hơn 0"
            )

        results = (
            self.vector_store
            .similarity_search_with_score(
                query=cleaned_query,
                k=limit,
            )
        )

        knowledge_results: list[
            dict[str, Any]
        ] = []

        for document, score in results:
            knowledge_results.append(
                {
                    "content": (
                        document.page_content
                    ),
                    "metadata": (
                        document.metadata
                    ),
                    "distance": float(score),
                }
            )

        return knowledge_results

    def count(self) -> int:
        """
        Trả về tổng số chunk trong collection.
        """

        stored_data = self.vector_store.get()

        return len(
            stored_data.get("ids", [])
        )

    def clear(self) -> None:
        """
        Xóa collection và khởi tạo lại.
        """

        self.vector_store.delete_collection()

        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(
                self.persist_directory
            ),
        )