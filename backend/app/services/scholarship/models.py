from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ScholarshipStatus = Literal[
    "eligible",
    "not_eligible",
    "insufficient_data",
]


class ScholarshipConditionResult(BaseModel):
    """
    Kết quả đánh giá của một điều kiện học bổng.
    """

    condition_code: str
    condition_name: str

    passed: bool

    actual_value: Any = None
    required_value: Any = None

    reason: str | None = None


class StudentScholarshipResult(BaseModel):
    """
    Kết quả đánh giá học bổng của một sinh viên.
    """

    student_id: str
    student_name: str

    status: ScholarshipStatus

    scholarship_type: str | None = None
    scholarship_level: str | None = None

    ranking_score: float | None = None

    missing_fields: list[str] = Field(
        default_factory=list
    )

    failed_conditions: list[str] = Field(
        default_factory=list
    )

    condition_results: list[
        ScholarshipConditionResult
    ] = Field(
        default_factory=list
    )

    recommendation: str = ""


class ScholarshipSummary(BaseModel):
    """
    Báo cáo tổng hợp kết quả đánh giá học bổng.
    """

    total_students: int

    eligible_count: int
    not_eligible_count: int
    insufficient_data_count: int

    eligible_rate: float
    not_eligible_rate: float
    insufficient_data_rate: float

    excellent_count: int = 0
    good_count: int = 0
    encouragement_count: int = 0

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


class ScholarshipEvaluationResponse(BaseModel):
    """
    Response hoàn chỉnh của chức năng
    đánh giá điều kiện học bổng.
    """

    success: bool

    dataset_name: str

    rule_set_code: str
    rule_set_name: str
    rule_set_version: str

    summary: ScholarshipSummary

    students: list[
        StudentScholarshipResult
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