from typing import Any

from pydantic import BaseModel, Field


class FusionRequest(BaseModel):
    filename: str
    category: str | None = None


class FusionSource(BaseModel):
    document: str
    page: int | None = None
    category: str | None = None


class FusionResponse(BaseModel):
    success: bool = True
    dataset_name: str

    data_findings: list[str] = Field(
        default_factory=list
    )

    knowledge_query: str = ""
    knowledge_answer: str = ""

    recommendations: list[str] = Field(
        default_factory=list
    )

    sources: list[FusionSource] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )