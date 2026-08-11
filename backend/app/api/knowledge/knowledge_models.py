from typing import Any

from pydantic import BaseModel, Field


class KnowledgeAskRequest(BaseModel):
    """
    Dữ liệu gửi lên khi người dùng hỏi
    Knowledge Assistant.
    """

    question: str = Field(
        ...,
        min_length=2,
        description="Câu hỏi về tri thức giáo dục VHU.",
        examples=[
            (
                "Quy định công nhận kết quả học tập "
                "và chuyển đổi tín chỉ áp dụng "
                "cho đối tượng nào?"
            )
        ],
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description=(
            "Số lượng đoạn tri thức gần nhất "
            "được lấy từ ChromaDB."
        ),
    )

    category: str | None = Field(
        default=None,
        description=(
            "Nhóm tài liệu cần tìm kiếm, "
            "ví dụ: dao_tao, hoc_bong, "
            "hoc_vu hoặc tot_nghiep."
        ),
        examples=["dao_tao"],
    )


class KnowledgeSearchRequest(BaseModel):
    """
    Dữ liệu gửi lên khi người dùng
    tìm kiếm tri thức bằng Semantic Search.
    """

    query: str = Field(
        ...,
        min_length=2,
        description="Nội dung cần tìm trong Knowledge Base.",
        examples=[
            "Điều kiện xét tốt nghiệp là gì?"
        ],
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description=(
            "Số đoạn tri thức liên quan nhất "
            "cần lấy từ ChromaDB."
        ),
    )

    category: str | None = Field(
        default=None,
        description=(
            "Nhóm tài liệu tùy chọn: "
            "dao_tao, hoc_bong, hoc_vu, "
            "tot_nghiep."
        ),
        examples=["tot_nghiep"],
    )


class KnowledgeSearchItemResponse(BaseModel):
    """
    Một kết quả Semantic Search.
    """

    chunk_id: str
    content: str
    source: str
    page: int | None = None
    category: str | None = None
    distance: float | None = None


class KnowledgeSearchResponse(BaseModel):
    """
    Danh sách kết quả Semantic Search.
    """

    success: bool = True
    query: str

    results: list[
        KnowledgeSearchItemResponse
    ] = Field(
        default_factory=list
    )

    retrieved_count: int = 0

class KnowledgeSourceResponse(BaseModel):
    """
    Một nguồn tài liệu được sử dụng
    để tạo câu trả lời.
    """

    source: str
    page: int | None = None
    category: str | None = None
    chunk_id: str
    distance: float | None = None


class KnowledgeAskResponse(BaseModel):
    """
    Kết quả trả về từ Knowledge Assistant.
    """

    success: bool = True
    question: str
    answer: str

    sources: list[KnowledgeSourceResponse] = Field(
        default_factory=list
    )

    retrieved_count: int = 0

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class KnowledgeHealthResponse(BaseModel):
    """
    Trạng thái Knowledge Base.
    """

    success: bool = True
    status: str
    vector_count: int


class KnowledgeDocumentResponse(BaseModel):
    """
    Thông tin một tài liệu trong Knowledge Base.
    """

    filename: str
    category: str
    file_type: str
    size_bytes: int


class KnowledgeDocumentListResponse(BaseModel):
    """
    Danh sách tài liệu đang có trong
    Knowledge Base.
    """

    success: bool = True

    documents: list[
        KnowledgeDocumentResponse
    ] = Field(
        default_factory=list
    )

    total_documents: int = 0
