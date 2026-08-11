from pathlib import Path
from typing import Any

from app.services.knowledge.document_loader import (
    DocumentLoader,
)
from app.services.knowledge.text_chunker import (
    TextChunker,
)
from app.services.knowledge.vector_store import (
    KnowledgeVectorStore,
)


class KnowledgeService:
    """
    Điều phối toàn bộ quy trình quản lý tri thức.

    Quy trình:
    1. Đọc tài liệu trong Knowledge Base
    2. Làm sạch và chia tài liệu thành chunks
    3. Tạo embedding và lưu vào ChromaDB
    4. Truy vấn tri thức theo ngữ nghĩa
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    def __init__(
        self,
        documents_directory: str | Path = (
            "knowledge_base/documents"
        ),
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> None:
        self.documents_directory = Path(
            documents_directory
        )

        self.documents_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.loader = DocumentLoader()

        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        self.vector_store = KnowledgeVectorStore()

    def list_documents(self) -> list[dict[str, Any]]:
        """
        Liệt kê các tài liệu hợp lệ trong Knowledge Base.
        """

        documents: list[dict[str, Any]] = []

        for path in self._get_document_paths():
            documents.append(
                {
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": path.stat().st_size,
                    "source": str(path),
                }
            )

        return documents

    def build_knowledge_base(
        self,
        rebuild: bool = False,
    ) -> dict[str, Any]:
        """
        Đọc và lập chỉ mục toàn bộ tài liệu.

        rebuild=True:
        - Xóa collection cũ
        - Tạo lại Knowledge Base từ đầu
        """

        if rebuild:
            self.vector_store.clear()

        document_paths = self._get_document_paths()

        total_documents = 0
        total_chunks = 0
        indexed_documents: list[dict[str, Any]] = []
        failed_documents: list[dict[str, str]] = []

        for path in document_paths:
            try:
                document = self.loader.load(path)

                chunks = self.chunker.split_document(
                    document
                )

                added_count = (
                    self.vector_store.add_chunks(
                        chunks
                    )
                )

                total_documents += 1
                total_chunks += added_count

                indexed_documents.append(
                    {
                        "filename": document["filename"],
                        "character_count": document[
                            "character_count"
                        ],
                        "chunks": added_count,
                    }
                )

            except Exception as error:
                failed_documents.append(
                    {
                        "filename": path.name,
                        "error": str(error),
                    }
                )

        return {
            "success": len(failed_documents) == 0,
            "documents_found": len(document_paths),
            "documents_indexed": total_documents,
            "chunks_indexed": total_chunks,
            "total_chunks_in_store": (
                self.vector_store.count()
            ),
            "indexed_documents": indexed_documents,
            "failed_documents": failed_documents,
        }

    def search(
        self,
        query: str,
        limit: int = 4,
    ) -> dict[str, Any]:
        """
        Truy vấn tri thức bằng semantic search.
        """

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "Câu truy vấn không được để trống"
            )

        results = self.vector_store.search(
            query=cleaned_query,
            limit=limit,
        )

        return {
            "query": cleaned_query,
            "result_count": len(results),
            "results": results,
        }

    def get_status(self) -> dict[str, Any]:
        """
        Trả về trạng thái hiện tại của Knowledge Base.
        """

        documents = self.list_documents()

        return {
            "documents_directory": str(
                self.documents_directory
            ),
            "document_count": len(documents),
            "vector_count": (
                self.vector_store.count()
            ),
            "documents": documents,
        }

    def clear_knowledge_base(
        self,
    ) -> dict[str, Any]:
        """
        Xóa toàn bộ vector đang lưu.

        Không xóa các file tài liệu gốc.
        """

        previous_count = self.vector_store.count()

        self.vector_store.clear()

        return {
            "success": True,
            "deleted_chunks": previous_count,
            "remaining_chunks": (
                self.vector_store.count()
            ),
        }

    def _get_document_paths(
        self,
    ) -> list[Path]:
        """
        Tìm tất cả tài liệu được hỗ trợ.
        """

        paths = [
            path
            for path in self.documents_directory.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower()
                in self.SUPPORTED_EXTENSIONS
            )
        ]

        return sorted(
            paths,
            key=lambda path: path.name.lower(),
        )