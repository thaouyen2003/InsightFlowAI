from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.knowledge.knowledge_service import (
    KnowledgeService,
)

from app.services.knowledge.rag_service import (
    KnowledgeRAGService,
)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


class KnowledgeIndexRequest(BaseModel):
    rebuild: bool = Field(
        default=False,
        description=(
            "Nếu true, hệ thống sẽ xóa vector cũ "
            "và lập chỉ mục lại toàn bộ tài liệu."
        ),
    )


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        description="Câu hỏi dùng để truy xuất tri thức.",
    )
    limit: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Số đoạn tri thức tối đa cần trả về.",
    )



class KnowledgeAskRequest(BaseModel):
    query: str = Field(
        min_length=1,
        description=(
            "Câu hỏi cần hệ thống trả lời "
            "dựa trên Knowledge Base."
        ),
    )

    limit: int = Field(
        default=4,
        ge=1,
        le=10,
        description=(
            "Số đoạn tri thức tối đa "
            "được truy xuất cho RAG."
        ),
    )



def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()


def get_rag_service() -> KnowledgeRAGService:
    return KnowledgeRAGService()


@router.get("/status")
def get_knowledge_status() -> dict[str, Any]:
    """
    Kiểm tra trạng thái Knowledge Base.

    Trả về:
    - Danh sách tài liệu
    - Số tài liệu
    - Số vector đang lưu
    """

    try:
        service = get_knowledge_service()
        status = service.get_status()

        return {
            "success": True,
            "status": status,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@router.post("/index")
def index_knowledge_base(
    request: KnowledgeIndexRequest,
) -> dict[str, Any]:
    """
    Đọc tài liệu, chia chunk, tạo embedding
    và lưu vào ChromaDB.
    """

    try:
        service = get_knowledge_service()

        result = service.build_knowledge_base(
            rebuild=request.rebuild
        )

        return {
            "success": result["success"],
            "message": (
                "Lập chỉ mục Knowledge Base hoàn tất"
            ),
            "result": result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@router.post("/search")
def search_knowledge(
    request: KnowledgeSearchRequest,
) -> dict[str, Any]:
    """
    Truy xuất các đoạn tri thức liên quan
    bằng semantic search.
    """

    try:
        service = get_knowledge_service()

        result = service.search(
            query=request.query,
            limit=request.limit,
        )

        return {
            "success": True,
            "result": result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@router.post("/ask")
def ask_knowledge_base(
    request: KnowledgeAskRequest,
) -> dict[str, Any]:
    """
    Trả lời câu hỏi bằng mô hình RAG.

    Quy trình:
    - Semantic search trong ChromaDB
    - Lấy các đoạn tri thức liên quan
    - Xây dựng prompt
    - Gọi Gemini
    - Trả về câu trả lời và nguồn
    """

    try:
        rag_service = get_rag_service()

        result = rag_service.answer(
            query=request.query,
            limit=request.limit,
        )

        return {
            "success": True,
            "message": (
                "Hệ thống RAG đã xử lý câu hỏi"
            ),
            "result": result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error
    

@router.delete("")
def clear_knowledge_base() -> dict[str, Any]:
    """
    Xóa toàn bộ vector trong Knowledge Base.

    Không xóa file PDF, DOCX hoặc TXT gốc.
    """

    try:
        service = get_knowledge_service()

        result = service.clear_knowledge_base()

        return {
            "success": True,
            "message": (
                "Đã xóa dữ liệu vector "
                "trong Knowledge Base"
            ),
            "result": result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error