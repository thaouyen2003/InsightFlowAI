import os
import time
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

    Mặc định sử dụng collection:
        vhu_knowledge

    Có thể truyền collection_name để tạo hoặc sử dụng
    collection riêng cho các thí nghiệm như
    chunking ablation.
    """

    COLLECTION_NAME = "vhu_knowledge"

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        # =====================================================
        # PERSIST DIRECTORY
        # =====================================================

        backend_dir = (
            Path(__file__)
            .resolve()
            .parents[3]
        )

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

        # =====================================================
        # CHROMADB CLIENT
        # =====================================================

        self.client = (
            chromadb.PersistentClient(
                path=str(
                    self.persist_dir
                )
            )
        )

        # =====================================================
        # COLLECTION NAME
        # =====================================================

        clean_collection_name = (
            str(collection_name).strip()
            if collection_name is not None
            else ""
        )

        self.collection_name = (
            clean_collection_name
            if clean_collection_name
            else self.COLLECTION_NAME
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": (
                        "Kho tri thức giáo dục "
                        "Đại học Văn Hiến"
                    ),
                },
            )
        )

        # =====================================================
        # EMBEDDING SERVICE
        # =====================================================

        self.embedding_service = (
            EmbeddingService()
        )

        # =====================================================
        # OPTIONAL DISTANCE THRESHOLD
        # =====================================================

        self.max_distance = (
            self._read_optional_float_env(
                "RAG_MAX_DISTANCE"
            )
        )

    # =========================================================
    # ADD CHUNKS
    # =========================================================

    def add_chunks(
        self,
        chunks: list[KnowledgeChunk],
        batch_size: int = 20,
        batch_delay_seconds: float = 0.0,
    ) -> int:
        """
        Sinh embedding và lưu chunks vào ChromaDB.

        Parameters
        ----------
        chunks:
            Danh sách KnowledgeChunk cần index.

        batch_size:
            Số chunk xử lý trong một batch.

        batch_delay_seconds:
            Thời gian chờ giữa các batch embedding.
            Hữu ích để tránh vượt quota Gemini trong
            các experiment build corpus lớn.

        Returns
        -------
        int
            Số chunk đã lưu thành công.
        """

        if not chunks:
            return 0

        if batch_size <= 0:
            raise ValueError(
                "batch_size phải lớn hơn 0."
            )

        if batch_delay_seconds < 0:
            raise ValueError(
                "batch_delay_seconds "
                "không được âm."
            )

        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.content.strip()
        ]

        if not valid_chunks:
            return 0

        stored_count = 0

        total_chunks = len(
            valid_chunks
        )

        for start in range(
            0,
            total_chunks,
            batch_size,
        ):
            batch = valid_chunks[
                start:start + batch_size
            ]

            # =================================================
            # PREPARE TEXTS
            # =================================================

            texts = [
                chunk.content.strip()
                for chunk in batch
            ]

            # =================================================
            # CREATE EMBEDDINGS
            # =================================================

            embeddings = (
                self.embedding_service
                .embed_documents(
                    texts
                )
            )

            if (
                len(embeddings)
                != len(batch)
            ):
                raise RuntimeError(
                    "Số embedding trả về "
                    "không khớp với số chunk "
                    "đầu vào."
                )

            # =================================================
            # FILTER INVALID EMBEDDINGS
            # =================================================

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
                print(
                    f"[{self.collection_name}] "
                    "Batch không có embedding hợp lệ."
                )

                continue

            # =================================================
            # UPSERT INTO CHROMADB
            # =================================================

            self.collection.upsert(
                ids=[
                    chunk.id
                    for chunk, _
                    in valid_items
                ],

                documents=[
                    chunk.content.strip()
                    for chunk, _
                    in valid_items
                ],

                metadatas=[
                    self._sanitize_metadata(
                        chunk.metadata
                    )
                    for chunk, _
                    in valid_items
                ],

                embeddings=[
                    embedding
                    for _, embedding
                    in valid_items
                ],
            )

            stored_count += len(
                valid_items
            )

            print(
                f"[{self.collection_name}] "
                "STORED:",
                stored_count,
                "/",
                total_chunks,
            )

            # =================================================
            # RATE-LIMIT THROTTLE
            # =================================================

            has_more_batches = (
                start + batch_size
                < total_chunks
            )

            if (
                batch_delay_seconds > 0
                and has_more_batches
            ):
                print(
                    f"[{self.collection_name}] "
                    f"Waiting "
                    f"{batch_delay_seconds:.1f}s "
                    "for embedding quota..."
                )

                time.sleep(
                    batch_delay_seconds
                )

        return stored_count

    # =========================================================
    # SEARCH
    # =========================================================

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
                "Nội dung truy vấn "
                "không được để trống."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        collection_count = (
            self.collection.count()
        )

        if collection_count <= 0:
            return []

        effective_top_k = min(
            top_k,
            collection_count,
        )

        clean_category = (
            category.strip()
            if (
                category
                and category.strip()
            )
            else None
        )

        # =====================================================
        # QUERY EMBEDDING
        # =====================================================

        query_embedding = (
            self.embedding_service
            .embed_query(
                clean_query
            )
        )

        if not query_embedding:
            raise RuntimeError(
                "Không thể tạo embedding "
                "cho truy vấn."
            )

        # =====================================================
        # CHROMADB QUERY
        # =====================================================

        query_args: dict[
            str,
            Any,
        ] = {
            "query_embeddings": [
                query_embedding
            ],

            "n_results":
                effective_top_k,

            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if clean_category is not None:
            query_args["where"] = {
                "category":
                    clean_category
            }

        response = (
            self.collection.query(
                **query_args
            )
        )

        ids = (
            self._first_result_list(
                response.get(
                    "ids"
                )
            )
        )

        documents = (
            self._first_result_list(
                response.get(
                    "documents"
                )
            )
        )

        metadatas = (
            self._first_result_list(
                response.get(
                    "metadatas"
                )
            )
        )

        distances = (
            self._first_result_list(
                response.get(
                    "distances"
                )
            )
        )

        results: list[
            VectorSearchResult
        ] = []

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
                self.max_distance
                is not None
                and normalized_distance
                is not None
                and normalized_distance
                > self.max_distance
            ):
                continue

            results.append(
                VectorSearchResult(
                    chunk_id=str(
                        chunk_id
                    ),

                    content=
                        clean_content,

                    metadata=dict(
                        metadata or {}
                    ),

                    distance=
                        normalized_distance,
                )
            )

        # =====================================================
        # SORT BY DISTANCE
        # =====================================================

        results.sort(
            key=lambda item: (
                item.distance
                if item.distance
                is not None
                else float("inf")
            )
        )

        return results

    # =========================================================
    # COUNT
    # =========================================================

    def count(
        self,
    ) -> int:
        """
        Trả về tổng số chunk trong collection.
        """

        return (
            self.collection.count()
        )

    # =========================================================
    # DELETE COLLECTION
    # =========================================================

    def delete_collection(
        self,
    ) -> None:
        """
        Xóa collection hiện tại.

        Hữu ích khi cần rebuild collection
        cho một chunking configuration.
        """

        existing_names = {
            collection.name
            for collection
            in self.client.list_collections()
        }

        if (
            self.collection_name
            not in existing_names
        ):
            return

        self.client.delete_collection(
            name=self.collection_name
        )

    # =========================================================
    # SANITIZE METADATA
    # =========================================================

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

        for key, value in (
            metadata.items()
        ):
            clean_key = str(
                key
            ).strip()

            if not clean_key:
                continue

            if isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool,
                ),
            ):
                sanitized[
                    clean_key
                ] = value

            elif value is not None:
                sanitized[
                    clean_key
                ] = str(
                    value
                )

        return sanitized

    # =========================================================
    # CHROMA HELPER
    # =========================================================

    @staticmethod
    def _first_result_list(
        value: Any,
    ) -> list[Any]:
        """
        Lấy danh sách kết quả của query đầu tiên
        từ response nested-list của ChromaDB.
        """

        if not value:
            return []

        first_item = value[0]

        if first_item is None:
            return []

        return list(
            first_item
        )

    # =========================================================
    # ENV HELPER
    # =========================================================

    @staticmethod
    def _read_optional_float_env(
        name: str,
    ) -> float | None:
        """
        Đọc biến môi trường dạng số thực.

        Trả về None nếu biến không tồn tại
        hoặc không hợp lệ.
        """

        raw_value = (
            os.getenv(
                name,
                "",
            )
            .strip()
        )

        if not raw_value:
            return None

        try:
            value = float(
                raw_value
            )

        except ValueError:
            print(
                f"INVALID {name}:",
                raw_value,
            )

            return None

        if value < 0:
            return None

        return value