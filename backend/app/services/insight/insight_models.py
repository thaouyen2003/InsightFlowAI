from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InsightType(str, Enum):
    INFORMATION = "information"
    POSITIVE = "positive"
    WARNING = "warning"
    CRITICAL = "critical"


class InsightSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InsightEvidence(BaseModel):
    """
    Bằng chứng dữ liệu tạo ra insight.
    """

    column: str | None = None
    related_columns: list[str] = Field(
        default_factory=list
    )

    affected_rows: int | None = None
    total_rows: int | None = None

    calculation: str | None = None

    sample_values: list[Any] = Field(
        default_factory=list
    )


class InsightObject(BaseModel):
    """
    Cấu trúc chuẩn của một insight trong InsightFlowAI.
    """

    id: str

    type: InsightType = InsightType.INFORMATION

    category: str = "general"

    title: str

    description: str

    metric: str | None = None

    value: float | int | str | None = None

    unit: str | None = None

    threshold: float | int | str | None = None

    severity: InsightSeverity = InsightSeverity.MEDIUM

    evidence: InsightEvidence = Field(
        default_factory=InsightEvidence
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    def to_rag_query(self) -> str:
        """
        Chuyển Insight Object thành truy vấn cho RAG.
        """

        query_parts = [
            f"Insight: {self.title}.",
            self.description,
            f"Loại insight: {self.type.value}.",
            f"Mức độ: {self.severity.value}.",
            f"Nhóm vấn đề: {self.category}.",
        ]

        if self.metric:
            query_parts.append(
                f"Chỉ số liên quan: {self.metric}."
            )

        if self.value is not None:
            value_text = str(self.value)

            if self.unit:
                value_text += self.unit

            query_parts.append(
                f"Giá trị phát hiện: {value_text}."
            )

        if self.threshold is not None:
            query_parts.append(
                f"Ngưỡng tham chiếu: {self.threshold}."
            )

        query_parts.append(
            (
                "Hãy tìm quy định, tri thức hoặc hướng dẫn "
                "liên quan và đề xuất hành động quản lý phù hợp."
            )
        )

        return "\n".join(query_parts)
    


class RecommendationObject(BaseModel):
    """
    Khuyến nghị hành động được sinh từ InsightObject.
    """

    id: str

    source_insight_id: str

    category: str

    title: str

    description: str

    priority: InsightSeverity = InsightSeverity.MEDIUM

    actions: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

class InsightCollection(BaseModel):
    """
    Kết quả từ Insight Engine.
    """

    dataset_name: str

    total_insights: int

    insights: list[InsightObject]

    recommendations: list[
        RecommendationObject
    ] = Field(
        default_factory=list
    )

    summary: dict[str, int] = Field(
        default_factory=dict
    )
