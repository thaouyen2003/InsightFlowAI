from fastapi import APIRouter, HTTPException

from app.api.knowledge.knowledge_models import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeHealthResponse,
    KnowledgeSourceResponse,
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