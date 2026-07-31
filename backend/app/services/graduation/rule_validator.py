from __future__ import annotations

from dataclasses import dataclass, field

from app.services.graduation.rule_schema import (
    GraduationRuleSchema,
)
from app.services.graduation.rules import (
    GraduationRuleSet,
)


@dataclass
class RuleValidationResult:
    is_valid: bool

    errors: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )


class GraduationRuleValidator:
    """
    Kiểm tra bộ luật được sinh từ RAG + LLM
    trước khi đưa vào Rule Engine.
    """

    MINIMUM_CONFIDENCE = 0.65

    @classmethod
    def validate(
        cls,
        rule_set: GraduationRuleSet,
    ) -> RuleValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        for rule in rule_set.rules:
            if not GraduationRuleSchema.is_supported(
                rule.field_name
            ):
                errors.append(
                    f"Luật '{rule.code}' sử dụng trường "
                    f"không được hỗ trợ: "
                    f"'{rule.field_name}'."
                )

            if (
                rule.source.document_name.strip()
                == ""
            ):
                errors.append(
                    f"Luật '{rule.code}' "
                    "không có tài liệu nguồn."
                )

            if (
                rule.source.evidence_text.strip()
                == ""
            ):
                errors.append(
                    f"Luật '{rule.code}' "
                    "không có đoạn trích dẫn chứng."
                )

            if rule.confidence < (
                cls.MINIMUM_CONFIDENCE
            ):
                warnings.append(
                    f"Luật '{rule.code}' có độ tin cậy "
                    f"thấp: {rule.confidence:.2f}."
                )

            if (
                rule.operator in {"in", "not_in"}
                and not rule.accepted_values
            ):
                errors.append(
                    f"Luật '{rule.code}' sử dụng "
                    f"operator '{rule.operator}' nhưng "
                    "accepted_values đang rỗng."
                )

            if (
                rule.operator
                in {
                    "greater_than_or_equal",
                    "less_than_or_equal",
                }
                and not isinstance(
                    rule.required_value,
                    (int, float),
                )
            ):
                errors.append(
                    f"Luật '{rule.code}' yêu cầu "
                    "required_value phải là số."
                )

        return RuleValidationResult(
            is_valid=not errors,
            errors=errors,
            warnings=warnings,
        )