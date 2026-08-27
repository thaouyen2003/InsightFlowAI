from fastapi import APIRouter, HTTPException

import json
from threading import Lock
from datetime import datetime

from app.api.knowledge.knowledge_models import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeHealthResponse,
    KnowledgeSourceResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchItemResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentListResponse,
)

from pathlib import Path
from app.services.rag.retriever import (
    KnowledgeRetriever,
)
from app.services.rag.rag_service import (
    RAGService,
)
from app.services.rag.vector_store import (
    VectorStore,
)


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge RAG"],
)

METRICS_LOCK = Lock()

BACKEND_DIR = Path(
    __file__
).resolve().parents[3]

METRICS_FILE = (
    BACKEND_DIR
    / "database"
    / "knowledge_metrics.json"
)


def read_query_count() -> int:
    """
    Đọc tổng số lượt truy vấn Knowledge AI.
    """

    if not METRICS_FILE.exists():
        return 0

    try:
        data = json.loads(
            METRICS_FILE.read_text(
                encoding="utf-8"
            )
        )

        return int(
            data.get(
                "ai_query_count",
                0,
            )
        )

    except (
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ):
        return 0

def increment_query_count() -> int:
    """
    Tăng số lượt truy vấn Knowledge AI
    mà không làm mất lịch sử activity.
    """

    with METRICS_LOCK:
        data = {
            "ai_query_count": 0,
            "activities": [],
        }

        if METRICS_FILE.exists():
            try:
                data = json.loads(
                    METRICS_FILE.read_text(
                        encoding="utf-8"
                    )
                )
            except (
                json.JSONDecodeError,
                ValueError,
                TypeError,
            ):
                pass

        current_count = int(
            data.get(
                "ai_query_count",
                0,
            )
        )

        new_count = current_count + 1

        data["ai_query_count"] = new_count

        METRICS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        METRICS_FILE.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return new_count
    
def save_knowledge_activity(
    question: str,
    category: str | None,
    retrieved_count: int,
) -> None:
    """
    Lưu lịch sử khai thác Knowledge Base.
    """

    with METRICS_LOCK:
        data = {
            "ai_query_count": 0,
            "activities": [],
        }

        if METRICS_FILE.exists():
            try:
                data = json.loads(
                    METRICS_FILE.read_text(
                        encoding="utf-8"
                    )
                )
            except (
                json.JSONDecodeError,
                ValueError,
                TypeError,
            ):
                pass

        activities = data.get(
            "activities",
            [],
        )

        activities.insert(
            0,
            {
                "question": question,
                "category": category,
                "retrieved_count":
                    retrieved_count,
                "created_at":
                    datetime.now().isoformat(
                        timespec="seconds"
                    ),
            },
        )

        # Chỉ giữ 50 hoạt động gần nhất
        data["activities"] = activities[:50]

        METRICS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        METRICS_FILE.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


@router.get(
    "/health",
    response_model=KnowledgeHealthResponse,
)
def knowledge_health() -> KnowledgeHealthResponse:
    """
    Kiểm tra trạng thái kho tri thức ChromaDB.
    """

    try:
        vector_store = VectorStore()

        return KnowledgeHealthResponse(
            success=True,
            status="ready",
            vector_count=vector_store.count(),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể kiểm tra Knowledge Base: "
                f"{error}"
            ),
        ) from error


@router.get(
    "/documents",
    response_model=KnowledgeDocumentListResponse,
)
def list_knowledge_documents() -> KnowledgeDocumentListResponse:
    """
    Liệt kê các tài liệu đang có trong Knowledge Base.
    """

    try:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        knowledge_base_dir = (
            backend_dir
            / "knowledge_base"
        )

        if not knowledge_base_dir.exists():
            return KnowledgeDocumentListResponse(
                success=True,
                documents=[],
                total_documents=0,
            )

        documents: list[
            KnowledgeDocumentResponse
        ] = []

        allowed_extensions = {
            ".pdf",
            ".docx",
            ".txt",
            ".md",
        }

        for category_dir in sorted(
            knowledge_base_dir.iterdir()
        ):
            if not category_dir.is_dir():
                continue

            if category_dir.name == "vector_store":
                continue

            category = category_dir.name

            for file_path in sorted(
                category_dir.iterdir()
            ):
                if not file_path.is_file():
                    continue

                suffix = file_path.suffix.lower()

                if suffix not in allowed_extensions:
                    continue

                documents.append(
                    KnowledgeDocumentResponse(
                        filename=file_path.name,
                        category=category,
                        file_type=suffix.lstrip("."),
                        size_bytes=file_path.stat().st_size,
                    )
                )

        return KnowledgeDocumentListResponse(
            success=True,
            documents=documents,
            total_documents=len(documents),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể đọc danh sách tài liệu: "
                f"{error}"
            ),
        ) from error


@router.get("/stats")
def get_knowledge_stats() -> dict:
    """
    Thống kê KPI cho Knowledge Management.
    """

    try:
        knowledge_base_dir = (
            BACKEND_DIR
            / "knowledge_base"
        )

        total_documents = 0

        categories: set[str] = set()

        allowed_extensions = {
            ".pdf",
            ".docx",
            ".txt",
            ".md",
        }

        if knowledge_base_dir.exists():
            for category_dir in (
                knowledge_base_dir.iterdir()
            ):
                if not category_dir.is_dir():
                    continue

                if (
                    category_dir.name
                    == "vector_store"
                ):
                    continue

                category_has_document = False

                for file_path in (
                    category_dir.iterdir()
                ):
                    if not file_path.is_file():
                        continue

                    if (
                        file_path.suffix.lower()
                        not in allowed_extensions
                    ):
                        continue

                    total_documents += 1
                    category_has_document = True

                if category_has_document:
                    categories.add(
                        category_dir.name
                    )

        return {
            "success": True,
            "total_documents":
                total_documents,
            "total_categories":
                len(categories),
            "ai_query_count":
                read_query_count(),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể lấy thống kê "
                "Knowledge Management: "
                f"{error}"
            ),
        ) from error

@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
)
def search_knowledge(
    payload: KnowledgeSearchRequest,
) -> KnowledgeSearchResponse:
    """
    Tìm kiếm tri thức bằng Semantic Search.

    Endpoint này chỉ truy xuất các đoạn tri thức
    liên quan nhất từ ChromaDB, không gọi LLM.
    """

    try:
        retriever = KnowledgeRetriever()

        results = retriever.retrieve(
            query=payload.query,
            top_k=payload.top_k,
            category=payload.category,
        )

        search_results = [
            KnowledgeSearchItemResponse(
                chunk_id=item.chunk_id,
                content=item.content,
                source=item.source,
                page=item.page,
                category=item.category,
                distance=item.distance,
            )
            for item in results
        ]

        return KnowledgeSearchResponse(
            success=True,
            query=payload.query,
            results=search_results,
            retrieved_count=len(search_results),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể tìm kiếm Knowledge Base: "
                f"{error}"
            ),
        ) from error


@router.get("/activities")
def get_knowledge_activities() -> dict:
    """
    Lấy lịch sử khai thác Knowledge Base.
    """

    try:
        if not METRICS_FILE.exists():
            return {
                "success": True,
                "activities": [],
                "total": 0,
            }

        data = json.loads(
            METRICS_FILE.read_text(
                encoding="utf-8"
            )
        )

        activities = data.get(
            "activities",
            [],
        )

        return {
            "success": True,
            "activities": activities,
            "total": len(activities),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể đọc Knowledge "
                f"Activity: {error}"
            ),
        ) from error



@router.post(
    "/ask",
    response_model=KnowledgeAskResponse,
)
def ask_knowledge(
    payload: KnowledgeAskRequest,
) -> KnowledgeAskResponse:
    """
    Trả lời câu hỏi dựa trên kho tri thức VHU.
    """

    try:
        service = RAGService()

        result = service.ask(
            question=payload.question,
            top_k=payload.top_k,
            category=payload.category,
        )

        increment_query_count()

        save_knowledge_activity(
            question=payload.question,
            category=payload.category,
            retrieved_count=result.retrieved_count,
        )

        sources = [
            KnowledgeSourceResponse(
                source=item.source,
                page=item.page,
                category=item.category,
                chunk_id=item.chunk_id,
                distance=item.distance,
            )
            for item in result.sources
        ]

        return KnowledgeAskResponse(
            success=True,
            question=result.question,
            answer=result.answer,
            sources=sources,
            retrieved_count=result.retrieved_count,
            metadata=result.metadata,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể xử lý câu hỏi tri thức: "
                f"{error}"
            ),
        ) from error


@router.get("/evaluation")
def get_rag_evaluation() -> dict:
    """
    Trả về kết quả benchmark RAG Retrieval.
    """

    try:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        result_path = (
            backend_dir
            / "tests"
            / "rag_benchmark_results.json"
        )

        if not result_path.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "Chưa có kết quả benchmark. "
                    "Hãy chạy rag_benchmark.py trước."
                ),
            )

        with open(
            result_path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return {
            "success": True,
            "evaluation": data,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể đọc kết quả "
                f"RAG Evaluation: {error}"
            ),
        ) from error