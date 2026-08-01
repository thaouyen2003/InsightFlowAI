from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


GraduationStatus = Literal[
    "eligible",
    "not_eligible",
    "insufficient_data",
]


class GraduationConditionResult(BaseModel):
    """
    Kết quả của một điều kiện xét tốt nghiệp.
    """

    condition_code: str
    condition_name: str

    passed: bool

    actual_value: Any = None
    required_value: Any = None

    reason: str | None = None


class StudentGraduationResult(BaseModel):
    """
    Kết quả đánh giá của một sinh viên.
    """

    student_id: str
    student_name: str

    status: GraduationStatus

    missing_fields: list[str] = Field(
        default_factory=list
    )

    failed_conditions: list[str] = Field(
        default_factory=list
    )

    condition_results: list[
        GraduationConditionResult
    ] = Field(
        default_factory=list
    )

    recommendation: str = ""


class GraduationSummary(BaseModel):
    """
    Báo cáo tổng hợp kết quả xét tốt nghiệp.
    """

    total_students: int

    eligible_count: int
    not_eligible_count: int
    insufficient_data_count: int

    eligible_rate: float
    not_eligible_rate: float
    insufficient_data_rate: float

    top_failed_conditions: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    top_missing_fields: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )


class GraduationEvaluationResponse(BaseModel):
    """
    Response hoàn chỉnh của chức năng
    đánh giá điều kiện tốt nghiệp.
    """

    success: bool

    dataset_name: str

    rule_set_code: str
    rule_set_name: str
    rule_set_version: str

    summary: GraduationSummary

    students: list[
        StudentGraduationResult
    ]

    sources: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )