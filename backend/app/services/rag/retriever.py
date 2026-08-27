import re
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

    # =========================================================
    # BASELINE RETRIEVAL
    # =========================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[RetrievedKnowledge]:
        """
        Baseline Retrieval.

        Tìm trực tiếp top_k đoạn tri thức
        dựa trên vector similarity.
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

        search_results = (
            self.vector_store.search(
                query=clean_query,
                top_k=top_k,
                category=category,
            )
        )

        retrieved_items: list[
            RetrievedKnowledge
        ] = []

        for result in search_results:
            retrieved_items.append(
                self._convert_result(result)
            )

        return retrieved_items

    # =========================================================
    # OPTIMIZED RETRIEVAL
    # =========================================================

    def retrieve_optimized(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
        candidate_k: int = 10,
    ) -> list[RetrievedKnowledge]:
        """
        Optimized Retrieval.

        Quy trình:
        1. Semantic retrieval lấy candidate_k candidates.
        2. Tính lexical similarity.
        3. Kết hợp semantic rank và lexical score.
        4. Rerank.
        5. Trả về top_k tốt nhất.

        Dùng cho Experiment 2.
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

        if candidate_k <= 0:
            raise ValueError(
                "candidate_k phải lớn hơn 0."
            )

        if candidate_k < top_k:
            candidate_k = top_k

        search_results = (
            self.vector_store.search(
                query=clean_query,
                top_k=candidate_k,
                category=category,
            )
        )

        candidates = [
            self._convert_result(result)
            for result in search_results
        ]

        if not candidates:
            return []

        reranked_items: list[
            tuple[
                float,
                float,
                int,
                RetrievedKnowledge,
            ]
        ] = []

        for semantic_rank, item in enumerate(
            candidates,
            start=1,
        ):
            lexical_score = self._lexical_score(
                query=clean_query,
                content=item.content,
            )

            semantic_score = (
                1.0 / semantic_rank
            )

            query_lower = clean_query.lower()
            content_lower = item.content.lower()

            phrase_boost = 0.0

            important_phrases = [
                "học phần bắt buộc",
                "học phần tự chọn",
                "học phần tiên quyết",
                "học phần học trước",
                "cảnh báo học vụ",
                "điểm trung bình tích lũy",
                "chuẩn ngoại ngữ",
                "chuẩn đầu ra tin học",
            ]

            for phrase in important_phrases:
                if (
                    phrase in query_lower
                    and phrase in content_lower
                ):
                    phrase_boost += 0.25

            combined_score = (
                0.40 * semantic_score
                + 0.45 * lexical_score
                + phrase_boost
            )

            reranked_items.append(
                (
                    combined_score,
                    lexical_score,
                    semantic_rank,
                    item,
                )
            )

        reranked_items.sort(
            key=lambda value: (
                value[0],
                value[1],
                -value[2],
            ),
            reverse=True,
        )

        return [
            item
            for (
                _combined_score,
                _lexical_score,
                _semantic_rank,
                item,
            ) in reranked_items[:top_k]
        ]

    # =========================================================
    # LEXICAL RERANKING
    # =========================================================

    def _tokenize(
        self,
        text: str,
    ) -> set[str]:
        """
        Chuẩn hóa văn bản thành tập token
        phục vụ lexical reranking.
        """

        normalized = (
            text
            .lower()
            .strip()
        )

        tokens = re.findall(
            r"\w+",
            normalized,
            flags=re.UNICODE,
        )

        stop_words = {
            "là",
            "của",
            "và",
            "có",
            "được",
            "trong",
            "như",
            "thế",
            "nào",
            "sinh",
            "viên",
            "theo",
            "để",
            "một",
            "những",
            "các",
            "cho",
            "với",
            "về",
            "thì",
            "khi",
            "hay",
            "hoặc",
        }

        return {
            token
            for token in tokens
            if (
                token not in stop_words
                and len(token) > 1
            )
        }

    def _lexical_score(
        self,
        query: str,
        content: str,
    ) -> float:
        """
        Tính độ trùng lexical giữa query
        và nội dung chunk.

        Score nằm trong khoảng 0 → 1.
        """

        query_tokens = (
            self._tokenize(query)
        )

        content_tokens = (
            self._tokenize(content)
        )

        if not query_tokens:
            return 0.0

        overlap = (
            query_tokens
            & content_tokens
        )

        return (
            len(overlap)
            / len(query_tokens)
        )

    # =========================================================
    # CONTEXT BUILDER
    # =========================================================

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
                        (
                            "Nội dung: "
                            f"{item.content}"
                        ),
                    ]
                )
            )

        return "\n\n".join(
            context_parts
        )

    # =========================================================
    # RESULT CONVERTER
    # =========================================================

    def _convert_result(
        self,
        result: VectorSearchResult,
    ) -> RetrievedKnowledge:
        """
        Chuyển VectorSearchResult
        thành RetrievedKnowledge.
        """

        metadata = dict(
            result.metadata or {}
        )

        page_value = metadata.get(
            "page"
        )

        try:
            page = (
                int(page_value)
                if page_value is not None
                else None
            )

        except (
            TypeError,
            ValueError,
        ):
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
                str(
                    metadata["category"]
                )
                if metadata.get(
                    "category"
                )
                else None
            ),
            distance=result.distance,
            metadata=metadata,
        )


    def retrieve_semantic_lexical(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
        candidate_k: int = 20,
    ) -> list[RetrievedKnowledge]:
        """
        Ablation Retrieval.

        Quy trình:
        1. Semantic retrieval lấy candidate_k candidates.
        2. Tính lexical similarity.
        3. Kết hợp semantic rank + lexical score.
        4. Không dùng phrase boost.
        5. Rerank và trả về top_k.
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

        if candidate_k <= 0:
            raise ValueError(
                "candidate_k phải lớn hơn 0."
            )

        if candidate_k < top_k:
            candidate_k = top_k

        search_results = (
            self.vector_store.search(
                query=clean_query,
                top_k=candidate_k,
                category=category,
            )
        )

        candidates = [
            self._convert_result(result)
            for result in search_results
        ]

        if not candidates:
            return []

        reranked_items = []

        for semantic_rank, item in enumerate(
            candidates,
            start=1,
        ):
            lexical_score = self._lexical_score(
                query=clean_query,
                content=item.content,
            )

            semantic_score = (
                1.0 / semantic_rank
            )

            combined_score = (
                0.40 * semantic_score
                + 0.45 * lexical_score
            )

            reranked_items.append(
                (
                    combined_score,
                    lexical_score,
                    semantic_rank,
                    item,
                )
            )

        reranked_items.sort(
            key=lambda value: (
                value[0],
                value[1],
                -value[2],
            ),
            reverse=True,
        )

        return [
            item
            for (
                _combined_score,
                _lexical_score,
                _semantic_rank,
                item,
            ) in reranked_items[:top_k]
        ]