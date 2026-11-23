import re
from typing import Any

from rank_bm25 import BM25Okapi

from app.services.rag.retriever import (
    RetrievedKnowledge,
)
from app.services.rag.vector_store import (
    VectorStore,
)


class BM25Retriever:
    """
    BM25 lexical retrieval baseline.

    Corpus được lấy trực tiếp từ ChromaDB để đảm bảo
    sử dụng cùng knowledge chunks với dense retrieval.
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

        self.documents: list[
            dict[str, Any]
        ] = []

        self.tokenized_corpus: list[
            list[str]
        ] = []

        self.bm25: BM25Okapi | None = None

        self._load_corpus()

    # =========================================================
    # TOKENIZATION
    # =========================================================

    @staticmethod
    def _tokenize(
        text: str,
    ) -> list[str]:
        """
        Tokenizer đơn giản cho BM25 baseline.

        - lowercase
        - giữ chữ và số
        - loại bỏ token một ký tự
        """

        clean_text = text.lower()

        tokens = re.findall(
            r"\b\w+\b",
            clean_text,
            flags=re.UNICODE,
        )

        return [
            token
            for token in tokens
            if len(token) > 1
        ]

    # =========================================================
    # LOAD CORPUS FROM CHROMADB
    # =========================================================

    def _load_corpus(
        self,
    ) -> None:
        """
        Lấy toàn bộ chunks trực tiếp từ ChromaDB.
        """

        response = (
            self.vector_store
            .collection
            .get(
                include=[
                    "documents",
                    "metadatas",
                ]
            )
        )

        ids = (
            response.get("ids")
            or []
        )

        documents = (
            response.get("documents")
            or []
        )

        metadatas = (
            response.get("metadatas")
            or []
        )

        self.documents = []

        self.tokenized_corpus = []

        for (
            chunk_id,
            content,
            metadata,
        ) in zip(
            ids,
            documents,
            metadatas,
            strict=False,
        ):
            clean_content = str(
                content or ""
            ).strip()

            if not clean_content:
                continue

            clean_metadata = dict(
                metadata or {}
            )

            tokens = self._tokenize(
                clean_content
            )

            if not tokens:
                continue

            self.documents.append(
                {
                    "chunk_id":
                        str(chunk_id),

                    "content":
                        clean_content,

                    "metadata":
                        clean_metadata,
                }
            )

            self.tokenized_corpus.append(
                tokens
            )

        if not self.documents:
            raise RuntimeError(
                "BM25 không tìm thấy corpus "
                "trong ChromaDB."
            )

        self.bm25 = BM25Okapi(
            self.tokenized_corpus
        )

        print(
            "[BM25] Loaded corpus:",
            len(self.documents),
            "chunks",
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[RetrievedKnowledge]:
        """
        BM25 retrieval.

        Có hỗ trợ category filter để đảm bảo
        evaluation setup tương ứng với dense baseline.
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

        if self.bm25 is None:
            raise RuntimeError(
                "BM25 index chưa được khởi tạo."
            )

        query_tokens = self._tokenize(
            clean_query
        )

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: (
                float(scores[index])
            ),
            reverse=True,
        )

        clean_category = (
            category.strip()
            if category
            and category.strip()
            else None
        )

        results: list[
            RetrievedKnowledge
        ] = []

        for index in ranked_indices:
            document = self.documents[
                index
            ]

            metadata = document[
                "metadata"
            ]

            document_category = (
                str(
                    metadata.get(
                        "category",
                        "",
                    )
                ).strip()
                or None
            )

            if (
                clean_category is not None
                and document_category
                != clean_category
            ):
                continue

            page_value = metadata.get(
                "page"
            )

            page: int | None = None

            if page_value is not None:
                try:
                    page = int(
                        page_value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    page = None

            source = str(
                metadata.get(
                    "source",
                    "",
                )
            ).strip()

            score = float(
                scores[index]
            )

            item_metadata = dict(
                metadata
            )

            item_metadata[
                "bm25_score"
            ] = score

            results.append(
                RetrievedKnowledge(
                    chunk_id=document[
                        "chunk_id"
                    ],

                    content=document[
                        "content"
                    ],

                    source=source,

                    page=page,

                    category=
                        document_category,

                    # BM25 không có vector distance
                    distance=None,

                    metadata=
                        item_metadata,
                )
            )

            if len(results) >= top_k:
                break

        return results