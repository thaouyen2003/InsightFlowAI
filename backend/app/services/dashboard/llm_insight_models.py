from typing import Literal

from pydantic import BaseModel, Field


class LLMInsightItem(BaseModel):
    """
    Một insight được LLM viết lại từ insight định lượng.

    LLM chỉ được diễn giải dữ liệu đã được backend tính toán,
    không tự tạo thêm số liệu.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )

    severity: Literal[
        "positive",
        "negative",
        "warning",
        "neutral",
    ] = "neutral"


class LLMRecommendationItem(BaseModel):
    """
    Một khuyến nghị được LLM tạo dựa trên insight có evidence.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )

    priority: Literal[
        "high",
        "medium",
        "low",
    ] = "medium"


class LLMInsightResponse(BaseModel):
    """
    Cấu trúc JSON bắt buộc mà LLM phải trả về.
    """

    executive_summary: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    key_findings: list[LLMInsightItem] = Field(
        default_factory=list,
        max_length=6,
    )

    recommendations: list[
        LLMRecommendationItem
    ] = Field(
        default_factory=list,
        max_length=4,
    )


class LLMInsightResult(BaseModel):
    """
    Kết quả cuối cùng của quá trình gọi LLM.

    Nếu LLM bị tắt hoặc gọi API thất bại,
    hệ thống vẫn trả về dashboard bình thường.
    """

    enabled: bool = False
    generated: bool = False

    model: str | None = None

    executive_summary: str | None = None

    key_findings: list[LLMInsightItem] = Field(
        default_factory=list
    )

    recommendations: list[
        LLMRecommendationItem
    ] = Field(
        default_factory=list
    )

    error: str | None = None