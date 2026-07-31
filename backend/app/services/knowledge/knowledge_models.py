from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeObject(BaseModel):
    """
    Đại diện cho một đơn vị tri thức được trích xuất
    từ insight và khuyến nghị.
    """

    id: str

    title: str

    content: str

    category: str

    source: str

    created_at: datetime = Field(
        default_factory=datetime.now
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class KnowledgeCollection(BaseModel):
    """
    Tập hợp các đơn vị tri thức của một dataset.
    """

    dataset_name: str

    total_knowledge: int

    items: list[KnowledgeObject] = Field(
        default_factory=list
    )