import os
from pathlib import Path
from typing import Any

import chromadb

from app.services.rag.embedding_service import (
    EmbeddingService,
)
from app.services.rag.text_chunker import (
    KnowledgeChunk,
)


class VectorSearchResult:
    """
    Kết quả truy xuất một chunk từ ChromaDB.
    """

    def __init__(
        self,
        chunk_id: str,
        content: str,
        metadata: dict[str, Any],
        distance: float | None,
    ) -> None:
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata
        self.distance = distance


class VectorStore:
    """
    Lưu trữ và truy xuất KnowledgeChunk bằng ChromaDB.
    """

    COLLECTION_NAME = "vhu_knowledge"

    def __init__(
        self,
        persist_dir: str | Path | None = None,
    ) -> None:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        self.persist_dir = (
            Path(persist_dir)
            if persist_dir is not None
            else backend_dir
            / "database"
            / "chroma"
        )

        self.persist_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir)
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={
                    "description": (
                        "Kho tri thức giáo dục "
                        "Đại học Văn Hiến"
                    ),
                },
            )
        )

        self.embedding_service = EmbeddingService()

        self.max_distance = (
            self._read_optional_float_env(
                "RAG_MAX_DISTANCE"
            )
        )

    def add_chunks(
        self,
        chunks: list[KnowledgeChunk],
        batch_size: int = 20,
    ) -> int:
        """
        Sinh embedding và lưu chunks vào ChromaDB.

        Chỉ lưu những chunk có nội dung và embedding
        hợp lệ.
        """

        if not chunks:
            return 0

        if batch_size <= 0:
            raise ValueError(
                "batch_size phải lớn hơn 0."
            )

        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.content.strip()
        ]

        if not valid_chunks:
            return 0

        stored_count = 0

        for start in range(
            0,
            len(valid_chunks),
            batch_size,
        ):
            batch = valid_chunks[
                start:start + batch_size
            ]

            texts = [
                chunk.content.strip()
                for chunk in batch
            ]

            embeddings = (
                self.embedding_service.embed_documents(
                    texts
                )
            )

            if len(embeddings) != len(batch):
                raise RuntimeError(
                    "Số embedding trả về không khớp "
                    "với số chunk đầu vào."
                )

            valid_items: list[
                tuple[
                    KnowledgeChunk,
                    list[float],
                ]
            ] = []

            for chunk, embedding in zip(
                batch,
                embeddings,
                strict=True,
            ):
                if not embedding:
                    continue

                valid_items.append(
                    (
                        chunk,
                        embedding,
                    )
                )

            if not valid_items:
                continue

            self.collection.upsert(
                ids=[
                    chunk.id
                    for chunk, _ in valid_items
                ],
                documents=[
                    chunk.content.strip()
                    for chunk, _ in valid_items
                ],
                metadatas=[
                    self._sanitize_metadata(
                        chunk.metadata
                    )
                    for chunk, _ in valid_items
                ],
                embeddings=[
                    embedding
                    for _, embedding in valid_items
                ],
            )

            stored_count += len(valid_items)

            print(
                "STORED:",
                stored_count,
                "/",
                len(valid_chunks),
            )

        return stored_count

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[VectorSearchResult]:
        """
        Truy xuất các chunk liên quan nhất.

        Có thể lọc theo category và loại bỏ kết quả
        vượt quá ngưỡng distance nếu RAG_MAX_DISTANCE
        được thiết lập trong .env.
        """

        clean_query = query.strip()

        if not clean_query:
            raise ValueError(
                "Nội dung truy vấn không được để trống."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        collection_count = self.collection.count()

        if collection_count <= 0:
            return []

        effective_top_k = min(
            top_k,
            collection_count,
        )

        clean_category = (
            category.strip()
            if category
            and category.strip()
            else None
        )

        query_embedding = (
            self.embedding_service.embed_query(
                clean_query
            )
        )

        if not query_embedding:
            raise RuntimeError(
                "Không thể tạo embedding cho truy vấn."
            )

        query_args: dict[str, Any] = {
            "query_embeddings": [
                query_embedding
            ],
            "n_results": effective_top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if clean_category is not None:
            query_args["where"] = {
                "category": clean_category
            }

        response = self.collection.query(
            **query_args
        )

        ids = self._first_result_list(
            response.get("ids")
        )

        documents = self._first_result_list(
            response.get("documents")
        )

        metadatas = self._first_result_list(
            response.get("metadatas")
        )

        distances = self._first_result_list(
            response.get("distances")
        )

        results: list[VectorSearchResult] = []

        for (
            chunk_id,
            content,
            metadata,
            distance,
        ) in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            clean_content = str(
                content or ""
            ).strip()

            if not clean_content:
                continue

            normalized_distance = (
                float(distance)
                if distance is not None
                else None
            )

            if (
                self.max_distance is not None
                and normalized_distance is not None
                and normalized_distance
                > self.max_distance
            ):
                continue

            results.append(
                VectorSearchResult(
                    chunk_id=str(chunk_id),
                    content=clean_content,
                    metadata=dict(
                        metadata or {}
                    ),
                    distance=normalized_distance,
                )
            )

        results.sort(
            key=lambda item: (
                item.distance
                if item.distance is not None
                else float("inf")
            )
        )

        return results

    def count(
        self,
    ) -> int:
        """
        Trả về tổng số chunk trong collection.
        """

        return self.collection.count()

    def _sanitize_metadata(
        self,
        metadata: dict[str, Any],
    ) -> dict[
        str,
        str | int | float | bool,
    ]:
        """
        ChromaDB chỉ nhận metadata kiểu đơn giản.
        """

        sanitized: dict[
            str,
            str | int | float | bool,
        ] = {}

        for key, value in metadata.items():
            clean_key = str(key).strip()

            if not clean_key:
                continue

            if isinstance(
                value,
                (str, int, float, bool),
            ):
                sanitized[
                    clean_key
                ] = value

            elif value is not None:
                sanitized[
                    clean_key
                ] = str(value)

        return sanitized

    @staticmethod
    def _first_result_list(
        value: Any,
    ) -> list[Any]:
        """
        Lấy danh sách kết quả của query đầu tiên
        từ response dạng nested list của ChromaDB.
        """

        if not value:
            return []

        first_item = value[0]

        if first_item is None:
            return []

        return list(first_item)

    @staticmethod
    def _read_optional_float_env(
        name: str,
    ) -> float | None:
        """
        Đọc biến môi trường dạng số thực.

        Trả về None nếu biến không tồn tại hoặc
        không hợp lệ.
        """

        raw_value = os.getenv(
            name,
            "",
        ).strip()

        if not raw_value:
            return None

        try:
            value = float(raw_value)
        except ValueError:
            print(
                f"INVALID {name}:",
                raw_value,
            )

            return None

        if value < 0:
            return None

        return value