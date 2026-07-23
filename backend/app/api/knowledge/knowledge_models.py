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