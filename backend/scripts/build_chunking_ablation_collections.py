import json
import sys
from pathlib import Path
from typing import Any

# =============================================================
# PROJECT PATH
# =============================================================

backend_dir = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(backend_dir),
)


from app.services.rag.document_loader import (
    LoadedDocument,
)
from app.services.rag.text_chunker import (
    KnowledgeChunk,
    TextChunker,
)
from app.services.rag.vector_store import (
    VectorStore,
)


# =============================================================
# CHUNKING CONFIGURATIONS
# =============================================================

CHUNKING_CONFIGS = [
    {
        "name": "chunk_400_75",
        "chunk_size": 400,
        "chunk_overlap": 75,
        "collection_name":
            "vhu_knowledge_chunk_400_75",
    },
    {
        "name": "chunk_800_150",
        "chunk_size": 800,
        "chunk_overlap": 150,
        "collection_name":
            "vhu_knowledge_chunk_800_150",
    },
    {
        "name": "chunk_1200_200",
        "chunk_size": 1200,
        "chunk_overlap": 200,
        "collection_name":
            "vhu_knowledge_chunk_1200_200",
    },
]


# =============================================================
# LOAD FROZEN CORPUS
# =============================================================


def load_frozen_documents(
    backend_dir: Path,
) -> list[LoadedDocument]:
    """
    Đọc frozen corpus tái dựng từ collection gốc.

    frozen_corpus_pages.json là source of truth
    cho chunking ablation.
    """

    frozen_file = (
        backend_dir
        / "app"
        / "services"
        / "evaluation"
        / "frozen_corpus_pages.json"
    )

    if not frozen_file.exists():
        raise FileNotFoundError(
            "Không tìm thấy frozen corpus: "
            f"{frozen_file}"
        )

    data = json.loads(
        frozen_file.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        data,
        list,
    ):
        raise ValueError(
            "frozen_corpus_pages.json "
            "phải là danh sách."
        )

    documents: list[
        LoadedDocument
    ] = []

    for page in data:
        content = str(
            page.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        source = page.get(
            "source"
        )

        page_number = page.get(
            "page"
        )

        category = page.get(
            "category"
        )

        path = page.get(
            "path"
        )

        if (
            source is None
            or page_number is None
        ):
            raise ValueError(
                "Frozen page thiếu "
                "source hoặc page."
            )

        documents.append(
            LoadedDocument(
                content=content,
                metadata={
                    "source":
                        str(source),

                    "page":
                        int(
                            page_number
                        ),

                    "category":
                        (
                            str(category)
                            if category
                            is not None
                            else "unknown"
                        ),

                    "path":
                        (
                            str(path)
                            if path
                            is not None
                            else ""
                        ),
                },
            )
        )

    return documents


# =============================================================
# VALIDATE FROZEN CORPUS
# =============================================================


def validate_frozen_corpus(
    documents: list[LoadedDocument],
) -> None:
    """
    Xác nhận frozen corpus tái tạo đúng
    cấu hình gốc 800/150.
    """

    if len(documents) != 57:
        raise RuntimeError(
            "Frozen corpus phải có đúng "
            "57 pages. "
            f"Actual={len(documents)}"
        )

    chunker = TextChunker(
        chunk_size=800,
        chunk_overlap=150,
    )

    chunks = (
        chunker.chunk_documents(
            documents
        )
    )

    if len(chunks) != 169:
        raise RuntimeError(
            "Frozen corpus không tái tạo "
            "đúng cấu hình gốc. "
            "Expected=169 chunks, "
            f"actual={len(chunks)}"
        )

    print(
        "Frozen corpus validation: OK"
    )

    print(
        "Reference pages:",
        len(documents),
    )

    print(
        "Reference chunks at 800/150:",
        len(chunks),
    )


# =============================================================
# GET EXISTING IDS
# =============================================================


def get_existing_chunk_ids(
    store: VectorStore,
) -> set[str]:
    """
    Lấy toàn bộ chunk IDs đã tồn tại
    trong collection.
    """

    response = (
        store.collection.get()
    )

    return {
        str(chunk_id)
        for chunk_id in (
            response.get("ids")
            or []
        )
    }


# =============================================================
# VALIDATE EXISTING CONTENT
# =============================================================


def validate_existing_chunks(
    expected_chunks: list[
        KnowledgeChunk
    ],
    store: VectorStore,
) -> None:
    """
    Kiểm tra các chunk đã tồn tại trong collection
    có cùng content với chunk expected hay không.

    Nếu ID giống nhưng content khác, dừng experiment
    thay vì resume trên dữ liệu không nhất quán.
    """

    response = store.collection.get(
        include=[
            "documents",
        ]
    )

    existing_ids = (
        response.get("ids")
        or []
    )

    existing_documents = (
        response.get("documents")
        or []
    )

    existing_content = {
        str(chunk_id):
            str(content or "").strip()
        for chunk_id, content in zip(
            existing_ids,
            existing_documents,
            strict=False,
        )
    }

    expected_content = {
        chunk.id:
            chunk.content.strip()
        for chunk in expected_chunks
    }

    mismatches = []

    unknown_ids = []

    for chunk_id, content in (
        existing_content.items()
    ):
        if chunk_id not in expected_content:
            unknown_ids.append(
                chunk_id
            )
            continue

        if (
            content
            != expected_content[
                chunk_id
            ]
        ):
            mismatches.append(
                chunk_id
            )

    if unknown_ids:
        raise RuntimeError(
            "Collection chứa chunk IDs "
            "không thuộc configuration hiện tại. "
            f"Examples={unknown_ids[:5]}"
        )

    if mismatches:
        raise RuntimeError(
            "Collection chứa chunk có "
            "content không khớp frozen corpus. "
            f"Examples={mismatches[:5]}"
        )


# =============================================================
# BUILD / RESUME ONE COLLECTION
# =============================================================


def build_collection(
    documents: list[LoadedDocument],
    persist_dir: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Build hoặc resume một chunking collection.

    Collection đã có chunk hợp lệ sẽ được giữ lại.
    Chỉ các chunk còn thiếu mới được embedding.
    """

    chunk_size = int(
        config["chunk_size"]
    )

    chunk_overlap = int(
        config["chunk_overlap"]
    )

    collection_name = str(
        config["collection_name"]
    )

    print(
        "\n"
        "========================================"
    )

    print(
        "BUILDING / RESUMING:",
        collection_name,
    )

    print(
        f"chunk_size={chunk_size}, "
        f"chunk_overlap={chunk_overlap}"
    )

    print(
        "========================================"
    )

    # =========================================================
    # GENERATE EXPECTED CHUNKS
    # =========================================================

    chunker = TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = (
        chunker.chunk_documents(
            documents
        )
    )

    expected_count = len(
        chunks
    )

    if not chunks:
        raise RuntimeError(
            f"{collection_name} "
            "không tạo ra chunk nào."
        )

    # =========================================================
    # REFERENCE SANITY CHECK
    # =========================================================

    if (
        chunk_size == 800
        and chunk_overlap == 150
        and expected_count != 169
    ):
        raise RuntimeError(
            "Sanity check failed: "
            "800/150 phải tạo đúng "
            "169 chunks. "
            f"Actual={expected_count}"
        )

    print(
        "Expected chunks:",
        expected_count,
    )

    # =========================================================
    # OPEN COLLECTION
    # =========================================================

    store = VectorStore(
        persist_dir=persist_dir,
        collection_name=
            collection_name,
    )

    existing_count = (
        store.count()
    )

    print(
        "Existing chunks:",
        existing_count,
    )

    # =========================================================
    # VALIDATE EXISTING DATA
    # =========================================================

    if existing_count > 0:
        validate_existing_chunks(
            expected_chunks=
                chunks,
            store=store,
        )

    existing_ids = (
        get_existing_chunk_ids(
            store
        )
    )

    # =========================================================
    # FIND MISSING CHUNKS
    # =========================================================

    missing_chunks = [
        chunk
        for chunk in chunks
        if chunk.id
        not in existing_ids
    ]

    missing_count = len(
        missing_chunks
    )

    print(
        "Missing chunks to embed:",
        missing_count,
    )

    # =========================================================
    # COMPLETE COLLECTION
    # =========================================================

    if missing_count == 0:
        print(
            "Collection already complete. "
            "Skipping embedding."
        )

    else:
        print(
            "Resuming embedding..."
        )

        store.add_chunks(
            chunks=missing_chunks,
            batch_size=20,
            batch_delay_seconds=15.0,
        )

    # =========================================================
    # FINAL CHECK
    # =========================================================

    final_count = (
        store.count()
    )

    print(
        "Final collection count:",
        final_count,
    )

    if (
        final_count
        != expected_count
    ):
        raise RuntimeError(
            "Collection chưa hoàn tất. "
            f"Expected={expected_count}, "
            f"actual={final_count}"
        )

    # =========================================================
    # FINAL CONTENT VALIDATION
    # =========================================================

    validate_existing_chunks(
        expected_chunks=chunks,
        store=store,
    )

    print(
        "Collection validation: OK"
    )

    return {
        "name":
            str(
                config["name"]
            ),

        "collection_name":
            collection_name,

        "chunk_size":
            chunk_size,

        "chunk_overlap":
            chunk_overlap,

        "expected_chunks":
            expected_count,

        "existing_before":
            existing_count,

        "embedded_this_run":
            missing_count,

        "final_chunks":
            final_count,

        "complete":
            True,
    }


# =============================================================
# SAVE SUMMARY
# =============================================================


def save_summary(
    backend_dir: Path,
    summaries: list[
        dict[str, Any]
    ],
) -> Path:
    """
    Lưu trạng thái chunking collections.
    """

    output_dir = (
        backend_dir
        / "app"
        / "services"
        / "evaluation"
        / "results"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir
        / "chunking_collection_summary.json"
    )

    output_file.write_text(
        json.dumps(
            summaries,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_file


# =============================================================
# MAIN
# =============================================================


def main() -> None:
    backend_dir = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    chroma_dir = (
        backend_dir
        / "database"
        / "chroma"
    )

    print(
        "Backend:",
        backend_dir,
    )

    print(
        "Chroma directory:",
        chroma_dir,
    )

    # =========================================================
    # ORIGINAL COLLECTION SAFETY CHECK
    # =========================================================

    original_store = VectorStore(
        persist_dir=chroma_dir,
        collection_name=
            "vhu_knowledge",
    )

    original_count = (
        original_store.count()
    )

    print(
        "\nOriginal collection:",
        original_store.collection.name,
    )

    print(
        "Original collection count:",
        original_count,
    )

    if (
        original_store.collection.name
        != "vhu_knowledge"
    ):
        raise RuntimeError(
            "Original collection name "
            "không đúng."
        )

    if original_count != 169:
        raise RuntimeError(
            "Original collection đã thay đổi. "
            "Expected=169, "
            f"actual={original_count}"
        )

    # =========================================================
    # LOAD FROZEN CORPUS
    # =========================================================

    print(
        "\nLoading frozen corpus..."
    )

    documents = (
        load_frozen_documents(
            backend_dir
        )
    )

    print(
        "Frozen pages loaded:",
        len(documents),
    )

    validate_frozen_corpus(
        documents
    )

    # =========================================================
    # BUILD / RESUME CONFIGURATIONS
    # =========================================================

    summaries: list[
        dict[str, Any]
    ] = []

    for config in (
        CHUNKING_CONFIGS
    ):
        summary = (
            build_collection(
                documents=documents,
                persist_dir=
                    chroma_dir,
                config=config,
            )
        )

        summaries.append(
            summary
        )

    # =========================================================
    # ORIGINAL COLLECTION FINAL SAFETY CHECK
    # =========================================================

    original_store = VectorStore(
        persist_dir=chroma_dir,
        collection_name=
            "vhu_knowledge",
    )

    final_original_count = (
        original_store.count()
    )

    if final_original_count != 169:
        raise RuntimeError(
            "Original collection bị thay đổi "
            "trong quá trình experiment. "
            "Expected=169, "
            f"actual={final_original_count}"
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    print(
        "\n"
        "========================================"
    )

    print(
        "CHUNKING ABLATION COLLECTION SUMMARY"
    )

    print(
        "========================================"
    )

    for item in summaries:
        print(
            f'{item["collection_name"]}: '
            f'{item["final_chunks"]}/'
            f'{item["expected_chunks"]} chunks '
            f'('
            f'{item["chunk_size"]}/'
            f'{item["chunk_overlap"]}'
            f')'
        )

    print(
        "\nOriginal collection:",
        final_original_count,
        "chunks",
    )

    output_file = (
        save_summary(
            backend_dir=
                backend_dir,
            summaries=
                summaries,
        )
    )

    print(
        "\nSaved summary:",
        output_file,
    )

    print(
        "\nCHUNKING ABLATION BUILD: DONE"
    )


if __name__ == "__main__":
    main()