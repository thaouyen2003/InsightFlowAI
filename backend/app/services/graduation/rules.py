from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


GraduationOperator = Literal[
    "greater_than_or_equal",
    "less_than_or_equal",
    "equal",
    "not_equal",
    "in",
    "not_in",
]


class GraduationRuleSource(BaseModel):
    """
    Nguồn tri thức chứng minh cho một điều kiện.

    Mỗi luật cần truy ngược được về tài liệu PDF,
    trang và đoạn văn liên quan.
    """

    document_name: str

    page_number: int | None = None

    chunk_id: str | None = None

    evidence_text: str = ""

    category: str = "tot_nghiep"


class GraduationRule(BaseModel):
    """
    Một luật xét điều kiện tốt nghiệp được
    trích xuất từ kho tri thức.
    """

    code: str

    name: str

    field_name: str

    operator: GraduationOperator

    required_value: Any

    accepted_values: list[str] = Field(
        default_factory=list
    )

    failure_message: str

    recommendation: str

    is_required: bool = True

    source: GraduationRuleSource

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    @field_validator("code", "field_name")
    @classmethod
    def validate_identifier(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "Mã luật và field_name không được rỗng."
            )

        return normalized


class GraduationRuleSet(BaseModel):
    """
    Bộ luật xét tốt nghiệp có cấu trúc.

    Bộ luật này được sinh từ tài liệu trong
    Knowledge Base, không viết cố định trong code.
    """

    rule_set_code: str

    rule_set_name: str

    version: str = "1.0"

    major: str | None = None

    cohort: str | None = None

    program: str | None = None

    effective_date: str | None = None

    rules: list[GraduationRule]

    source_documents: list[str] = Field(
        default_factory=list
    )

    extraction_notes: list[str] = Field(
        default_factory=list
    )

    generated_by: str = "rag_rule_extractor"

    @field_validator("rules")
    @classmethod
    def validate_rules(
        cls,
        rules: list[GraduationRule],
    ) -> list[GraduationRule]:
        if not rules:
            raise ValueError(
                "Bộ luật phải có ít nhất một điều kiện."
            )

        rule_codes = [
            rule.code
            for rule in rules
        ]

        duplicate_codes = {
            code
            for code in rule_codes
            if rule_codes.count(code) > 1
        }

        if duplicate_codes:
            raise ValueError(
                "Mã luật bị trùng: "
                + ", ".join(
                    sorted(duplicate_codes)
                )
            )

        return rules