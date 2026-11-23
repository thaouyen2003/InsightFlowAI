from app.services.rag.bm25_retriever import (
    BM25Retriever,
)
from app.services.rag.retriever import (
    KnowledgeRetriever,
    RetrievedKnowledge,
)


class HybridRetriever:
    """
    Hybrid retrieval bằng Reciprocal Rank Fusion (RRF).

    Quy trình:
    1. Dense retrieval lấy Top-N.
    2. BM25 retrieval lấy Top-N.
    3. Hợp nhất ranking bằng RRF.
    4. Trả về Top-K cuối cùng.
    """

    def __init__(
        self,
        dense_retriever: KnowledgeRetriever,
        bm25_retriever: BM25Retriever,
        rrf_k: int = 60,
    ) -> None:
        self.dense_retriever = (
            dense_retriever
        )

        self.bm25_retriever = (
            bm25_retriever
        )

        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 20,
        category: str | None = None,
    ) -> list[RetrievedKnowledge]:
        """
        Hybrid Dense + BM25 retrieval bằng RRF.
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

        dense_results = (
            self.dense_retriever.retrieve(
                query=clean_query,
                top_k=candidate_k,
                category=category,
            )
        )

        bm25_results = (
            self.bm25_retriever.retrieve(
                query=clean_query,
                top_k=candidate_k,
                category=category,
            )
        )

        scores: dict[
            str,
            float,
        ] = {}

        items: dict[
            str,
            RetrievedKnowledge,
        ] = {}

        dense_ranks: dict[
            str,
            int,
        ] = {}

        bm25_ranks: dict[
            str,
            int,
        ] = {}

        # =====================================================
        # DENSE RRF CONTRIBUTION
        # =====================================================

        for rank, item in enumerate(
            dense_results,
            start=1,
        ):
            chunk_id = item.chunk_id

            scores[
                chunk_id
            ] = (
                scores.get(
                    chunk_id,
                    0.0,
                )
                + 1.0
                / (
                    self.rrf_k
                    + rank
                )
            )

            items[
                chunk_id
            ] = item

            dense_ranks[
                chunk_id
            ] = rank

        # =====================================================
        # BM25 RRF CONTRIBUTION
        # =====================================================

        for rank, item in enumerate(
            bm25_results,
            start=1,
        ):
            chunk_id = item.chunk_id

            scores[
                chunk_id
            ] = (
                scores.get(
                    chunk_id,
                    0.0,
                )
                + 1.0
                / (
                    self.rrf_k
                    + rank
                )
            )

            if chunk_id not in items:
                items[
                    chunk_id
                ] = item

            bm25_ranks[
                chunk_id
            ] = rank

        # =====================================================
        # SORT
        # =====================================================

        ranked_ids = sorted(
            scores.keys(),
            key=lambda chunk_id: (
                scores[chunk_id],
                -min(
                    dense_ranks.get(
                        chunk_id,
                        10**9,
                    ),
                    bm25_ranks.get(
                        chunk_id,
                        10**9,
                    ),
                ),
            ),
            reverse=True,
        )

        results: list[
            RetrievedKnowledge
        ] = []

        for chunk_id in ranked_ids[
            :top_k
        ]:
            source_item = items[
                chunk_id
            ]

            metadata = dict(
                source_item.metadata
            )

            metadata[
                "rrf_score"
            ] = scores[
                chunk_id
            ]

            metadata[
                "dense_rank"
            ] = dense_ranks.get(
                chunk_id
            )

            metadata[
                "bm25_rank"
            ] = bm25_ranks.get(
                chunk_id
            )

            results.append(
                RetrievedKnowledge(
                    chunk_id=
                        source_item.chunk_id,

                    content=
                        source_item.content,

                    source=
                        source_item.source,

                    page=
                        source_item.page,

                    category=
                        source_item.category,

                    distance=
                        source_item.distance,

                    metadata=
                        metadata,
                )
            )

        return results