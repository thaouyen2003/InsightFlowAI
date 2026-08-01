from typing import Any

from pydantic import BaseModel, Field

from app.services.rag.vector_store import (
    VectorSearchResult,
    VectorStore,
)


class RetrievedKnowledge(BaseModel):
    """
    Một đoạn tri thức được truy xuất từ ChromaDB.
    """

    chunk_id: str
    content: str
    source: str
    page: int | None = None
    category: str | None = None
    distance: float | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class KnowledgeRetriever:
    """
    Truy xuất các đoạn tri thức liên quan nhất
    từ Vector Store.
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.vector_store = (
            vector_store
            if vector_store is not None
            else VectorStore()
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[RetrievedKnowledge]:
        """
        Tìm các đoạn tri thức liên quan đến câu hỏi.
        """

        clean_query = query.strip()

        if not clean_query:
            raise ValueError(
                "Câu hỏi không được để trống."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        search_results = self.vector_store.search(
            query=clean_query,
            top_k=top_k,
            category=category,
        )

        retrieved_items: list[
            RetrievedKnowledge
        ] = []

        for result in search_results:
            retrieved_items.append(
                self._convert_result(result)
            )

        return retrieved_items

    def build_context(
        self,
        retrieved_items: list[
            RetrievedKnowledge
        ],
    ) -> str:
        """
        Ghép các đoạn tri thức thành context
        để gửi cho mô hình ngôn ngữ.
        """

        if not retrieved_items:
            return ""

        context_parts: list[str] = []

        for index, item in enumerate(
            retrieved_items,
            start=1,
        ):
            source_label = item.source

            if item.page is not None:
                source_label += (
                    f", trang {item.page}"
                )

            if item.category:
                source_label += (
                    f", nhóm {item.category}"
                )

            context_parts.append(
                "\n".join(
                    [
                        f"[Tài liệu {index}]",
                        f"Nguồn: {source_label}",
                        f"Nội dung: {item.content}",
                    ]
                )
            )

        return "\n\n".join(context_parts)

    def _convert_result(
        self,
        result: VectorSearchResult,
    ) -> RetrievedKnowledge:
        metadata = dict(
            result.metadata or {}
        )

        page_value = metadata.get("page")

        try:
            page = (
                int(page_value)
                if page_value is not None
                else None
            )
        except (TypeError, ValueError):
            page = None

        return RetrievedKnowledge(
            chunk_id=result.chunk_id,
            content=result.content,
            source=str(
                metadata.get(
                    "source",
                    "Không xác định",
                )
            ),
            page=page,
            category=(
                str(metadata["category"])
                if metadata.get("category")
                else None
            ),
            distance=result.distance,
            metadata=metadata,
        )