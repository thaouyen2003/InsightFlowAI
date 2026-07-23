import shutil
from pathlib import Path

from app.services.rag.document_loader import (
    DocumentLoader,
)
from app.services.rag.text_chunker import (
    TextChunker,
)
from app.services.rag.vector_store import (
    VectorStore,
)


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]

    knowledge_base_dir = (
        backend_dir / "knowledge_base"
    )

    chroma_dir = (
        backend_dir / "database" / "chroma"
    )

    print("KNOWLEDGE BASE:", knowledge_base_dir)
    print("CHROMA DIR:", chroma_dir)

    if not knowledge_base_dir.exists():
        raise FileNotFoundError(
            f"Không tìm thấy thư mục: "
            f"{knowledge_base_dir}"
        )

    # if chroma_dir.exists():
    #     print("Đang xóa ChromaDB cũ...")
    #     shutil.rmtree(chroma_dir)

    print("Đang tải tài liệu...")
    loader = DocumentLoader(
        knowledge_base_dir
    )

    documents = loader.load_all()

    print(
        "Số trang tài liệu đã tải:",
        len(documents),
    )

    if not documents:
        raise RuntimeError(
            "Không tìm thấy tài liệu PDF "
            "trong Knowledge Base."
        )

    print("Đang chia tài liệu thành chunks...")
    chunker = TextChunker(
        chunk_size=800,
        chunk_overlap=150,
    )

    chunks = chunker.chunk_documents(
        documents
    )

    print(
        "Số chunks đã tạo:",
        len(chunks),
    )

    print("Kiểm tra đầu 5 chunks:")

    for index, chunk in enumerate(
        chunks[:5],
        start=1,
    ):
        print(
            f"\n--- CHUNK {index} ---"
        )
        print(
            repr(chunk.content[:150])
        )

    print("\nĐang tạo embeddings và lưu ChromaDB...")

    vector_store = VectorStore(
        persist_dir=chroma_dir
    )

    stored_count = vector_store.add_chunks(
        chunks=chunks,
        batch_size=20,
    )

    print(
        "Số chunks đã lưu:",
        stored_count,
    )

    print(
        "Tổng số vector trong collection:",
        vector_store.count(),
    )

    print("\nREBUILD KNOWLEDGE BASE: DONE")


if __name__ == "__main__":
    main()