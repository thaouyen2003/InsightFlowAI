import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.services.rag.document_loader import DocumentLoader
from app.services.rag.text_chunker import TextChunker
from app.services.rag.vector_store import VectorStore


def main() -> None:
    knowledge_base_dir = (
        backend_dir / "knowledge_base"
    )

    target_categories = {
        "hoc_vu",
        "tot_nghiep",
    }

    loader = DocumentLoader(
        knowledge_base_dir
    )

    documents = loader.load_all()

    selected_documents = [
        document
        for document in documents
        if document.metadata.get("category")
        in target_categories
    ]

    print(
        "SELECTED DOCUMENTS:",
        len(selected_documents),
    )

    chunker = TextChunker(
        chunk_size=800,
        chunk_overlap=150,
    )

    chunks = chunker.chunk_documents(
        selected_documents
    )

    print("SELECTED CHUNKS:", len(chunks))

    for chunk in chunks[:5]:
        print(
            chunk.metadata.get("category"),
            chunk.metadata.get("source"),
        )

    store = VectorStore()

    stored_count = store.add_chunks(
        chunks=chunks,
        batch_size=10,
    )

    print("STORED:", stored_count)
    print("TOTAL:", store.count())


if __name__ == "__main__":
    main()