from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

import pandas as pd

from app.services.scholarship.models import (
    ScholarshipConditionResult,
    StudentScholarshipResult,
)
from app.services.scholarship.rules import (
    ScholarshipRule,
    ScholarshipRuleSet,
)


class ScholarshipEvaluator:
    """
    Đánh giá điều kiện học bổng của từng sinh viên.

    Evaluator không chứa các ngưỡng nghiệp vụ
    được viết cứng.

    Mọi điều kiện được truyền vào thông qua
    ScholarshipRuleSet trích xuất từ Knowledge Base.
    """

    @staticmethod
    def is_missing(
        value: Any,
    ) -> bool:
        """
        Kiểm tra giá trị có bị thiếu hay không.
        """

        if value is None:
            return True

        try:
            if pd.isna(value):
                return True
        except (TypeError, ValueError):
            pass

        if isinstance(value, str):
            return not value.strip()

        return False

    @classmethod
    def normalize_status_value(
        cls,
        value: Any,
    ) -> str:
        """
        Chuẩn hóa giá trị trạng thái để so sánh.

        Ví dụ:
        - "Đã hoàn thành" -> "da hoan thanh"
        - "Không bị kỷ luật" -> "khong bi ky luat"
        - "PASSED" -> "passed"
        """

        if cls.is_missing(value):
            return ""

        text = str(value).strip().lower()

        text = text.replace(
            "đ",
            "d",
        )

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = "".join(
            character
            for character in text
            if not unicodedata.combining(
                character
            )
        )

        text = re.sub(
            r"[^a-z0-9]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @classmethod
    def to_number(
        cls,
        value: Any,
    ) -> float | None:
        """
        Chuyển giá trị thành số thực.

        Hỗ trợ:
        - 3.2
        - "3.2"
        - "3,2"
        - "85 điểm"
        - "GPA: 3.5"
        """

        if cls.is_missing(value):
            return None

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, (int, float)):
            number = float(value)

            if math.isnan(number):
                return None

            return number

        text = str(value).strip()

        text = text.replace(
            ",",
            ".",
        )

        try:
            number = float(text)

            if math.isnan(number):
                return None

            return number
        except ValueError:
            pass

        number_match = re.search(
            r"-?\d+(?:\.\d+)?",
            text,
        )

        if number_match is None:
            return None

        try:
            return float(
                number_match.group()
            )
        except ValueError:
            return None

    @classmethod
    def compare_equal(
        cls,
        actual_value: Any,
        required_value: Any,
    ) -> bool:
        """
        So sánh hai giá trị.

        Nếu cả hai có thể chuyển thành số,
        hệ thống thực hiện so sánh số.
        Nếu không, hệ thống so sánh chuỗi
        đã được chuẩn hóa.
        """

        actual_number = cls.to_number(
            actual_value
        )

        required_number = cls.to_number(
            required_value
        )

        if (
            actual_number is not None
            and required_number is not None
        ):
            return math.isclose(
                actual_number,
                required_number,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )

        return (
            cls.normalize_status_value(
                actual_value
            )
            == cls.normalize_status_value(
                required_value
            )
        )

    @classmethod
    def evaluate_rule(
        cls,
        *,
        value: Any,
        rule: ScholarshipRule,
    ) -> ScholarshipConditionResult:
        """
        Đánh giá một giá trị dựa trên một luật
        học bổng.

        Operator được hỗ trợ:
        - greater_than_or_equal
        - less_than_or_equal
        - equal
        - not_equal
        - in
        - not_in
        """

        passed = False

        if rule.operator == "greater_than_or_equal":
            actual_number = cls.to_number(
                value
            )

            required_number = cls.to_number(
                rule.required_value
            )

            passed = (
                actual_number is not None
                and required_number is not None
                and actual_number
                >= required_number
            )

        elif rule.operator == "less_than_or_equal":
            actual_number = cls.to_number(
                value
            )

            required_number = cls.to_number(
                rule.required_value
            )

            passed = (
                actual_number is not None
                and required_number is not None
                and actual_number
                <= required_number
            )

        elif rule.operator == "equal":
            passed = cls.compare_equal(
                actual_value=value,
                required_value=(
                    rule.required_value
                ),
            )

        elif rule.operator == "not_equal":
            passed = not cls.compare_equal(
                actual_value=value,
                required_value=(
                    rule.required_value
                ),
            )

        elif rule.operator == "in":
            normalized_value = (
                cls.normalize_status_value(
                    value
                )
            )

            normalized_accepted_values = {
                cls.normalize_status_value(
                    accepted_value
                )
                for accepted_value
                in rule.accepted_values
            }

            if not normalized_accepted_values:
                normalized_required_value = (
                    cls.normalize_status_value(
                        rule.required_value
                    )
                )

                if normalized_required_value:
                    normalized_accepted_values.add(
                        normalized_required_value
                    )

            passed = (
                normalized_value
                in normalized_accepted_values
            )

        elif rule.operator == "not_in":
            normalized_value = (
                cls.normalize_status_value(
                    value
                )
            )

            normalized_rejected_values = {
                cls.normalize_status_value(
                    rejected_value
                )
                for rejected_value
                in rule.accepted_values
            }

            if not normalized_rejected_values:
                normalized_required_value = (
                    cls.normalize_status_value(
                        rule.required_value
                    )
                )

                if normalized_required_value:
                    normalized_rejected_values.add(
                        normalized_required_value
                    )

            passed = (
                normalized_value
                not in normalized_rejected_values
            )

        else:
            raise ValueError(
                "Operator chưa được hỗ trợ: "
                f"{rule.operator}"
            )

        reason = (
            None
            if passed
            else rule.failure_message
        )

        return ScholarshipConditionResult(
            condition_code=rule.code,
            condition_name=rule.name,
            passed=passed,
            actual_value=(
                None
                if cls.is_missing(value)
                else value
            ),
            required_value=rule.required_value,
            reason=reason,
        )

    @classmethod
    def evaluate_student(
        cls,
        student: pd.Series | dict[str, Any],
        *,
        rule_set: ScholarshipRuleSet,
    ) -> StudentScholarshipResult:
        """
        Đánh giá một sinh viên bằng bộ luật
        học bổng.

        Trạng thái đầu ra:
        - eligible
        - not_eligible
        - insufficient_data
        """

        if not isinstance(
            student,
            (pd.Series, dict),
        ):
            raise TypeError(
                "student phải là pandas.Series "
                "hoặc dict."
            )

        if not isinstance(
            rule_set,
            ScholarshipRuleSet,
        ):
            raise TypeError(
                "rule_set phải là "
                "ScholarshipRuleSet."
            )

        if not rule_set.rules:
            raise ValueError(
                "Không thể đánh giá vì bộ luật rỗng."
            )

        student_data = dict(student)

        student_id_value = student_data.get(
            "student_id"
        )

        student_name_value = student_data.get(
            "student_name"
        )

        student_id = (
            ""
            if cls.is_missing(student_id_value)
            else str(student_id_value).strip()
        )

        student_name = (
            ""
            if cls.is_missing(student_name_value)
            else str(student_name_value).strip()
        )

        missing_fields: list[str] = []
        failed_conditions: list[str] = []
        recommendations: list[str] = []

        condition_results: list[
            ScholarshipConditionResult
        ] = []

        for rule in rule_set.rules:
            field_exists = (
                rule.field_name
                in student_data
            )

            value = student_data.get(
                rule.field_name
            )

            value_is_missing = (
                not field_exists
                or cls.is_missing(value)
            )

            if value_is_missing:
                if rule.is_required:
                    missing_fields.append(
                        rule.field_name
                    )

                continue

            condition_result = (
                cls.evaluate_rule(
                    value=value,
                    rule=rule,
                )
            )

            condition_results.append(
                condition_result
            )

            if not condition_result.passed:
                failed_conditions.append(
                    rule.failure_message
                )

                if rule.recommendation:
                    recommendations.append(
                        rule.recommendation
                    )

        missing_fields = list(
            dict.fromkeys(missing_fields)
        )

        failed_conditions = list(
            dict.fromkeys(failed_conditions)
        )

        recommendations = list(
            dict.fromkeys(recommendations)
        )

        if missing_fields:
            status = "insufficient_data"

            missing_fields_text = ", ".join(
                missing_fields
            )

            recommendation = (
                "Chưa đủ dữ liệu để kết luận. "
                "Cần bổ sung các trường: "
                f"{missing_fields_text}."
            )

            if recommendations:
                recommendation += " " + " ".join(
                    recommendations
                )

        elif failed_conditions:
            status = "not_eligible"

            if recommendations:
                recommendation = " ".join(
                    recommendations
                )
            else:
                recommendation = (
                    "Sinh viên cần hoàn thành "
                    "các điều kiện chưa đạt trước "
                    "khi đăng ký xét học bổng."
                )

        else:
            status = "eligible"

            recommendation = (
                "Sinh viên đáp ứng các điều kiện "
                "học bổng được trích xuất từ kho "
                "tri thức. Kết quả này chỉ mang "
                "tính hỗ trợ và cần được đơn vị "
                "có thẩm quyền kiểm tra trước khi "
                "công nhận chính thức."
            )

        return StudentScholarshipResult(
            student_id=student_id,
            student_name=student_name,
            status=status,
            scholarship_type=(
                rule_set.scholarship_type
            ),
            scholarship_level=None,
            ranking_score=None,
            missing_fields=missing_fields,
            failed_conditions=failed_conditions,
            condition_results=condition_results,
            recommendation=recommendation,
        )

    @classmethod
    def evaluate_dataframe(
        cls,
        df: pd.DataFrame,
        *,
        rule_set: ScholarshipRuleSet,
    ) -> list[StudentScholarshipResult]:
        """
        Đánh giá toàn bộ sinh viên trong DataFrame.

        DataFrame phải được chuẩn hóa tên cột
        trước khi truyền vào hàm.
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "df phải là pandas.DataFrame."
            )

        if df.empty:
            return []

        results: list[
            StudentScholarshipResult
        ] = []

        for _, student_row in df.iterrows():
            student_result = (
                cls.evaluate_student(
                    student=student_row,
                    rule_set=rule_set,
                )
            )

            results.append(
                student_result
            )

        return results