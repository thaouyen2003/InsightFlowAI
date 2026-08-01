from __future__ import annotations

from collections import Counter

from app.services.graduation.models import (
    GraduationSummary,
    StudentGraduationResult,
)


class GraduationSummaryBuilder:
    """
    Tổng hợp kết quả đánh giá tốt nghiệp
    của toàn bộ sinh viên.
    """

    @classmethod
    def build(
        cls,
        results: list[
            StudentGraduationResult
        ],
    ) -> GraduationSummary:
        """
        Tạo báo cáo tổng hợp từ danh sách
        kết quả đánh giá từng sinh viên.
        """

        total_students = len(results)

        eligible_count = sum(
            1
            for result in results
            if result.status == "eligible"
        )

        not_eligible_count = sum(
            1
            for result in results
            if result.status == "not_eligible"
        )

        insufficient_data_count = sum(
            1
            for result in results
            if result.status == "insufficient_data"
        )

        if total_students > 0:
            eligible_rate = round(
                eligible_count
                / total_students
                * 100,
                2,
            )

            not_eligible_rate = round(
                not_eligible_count
                / total_students
                * 100,
                2,
            )

            insufficient_data_rate = round(
                insufficient_data_count
                / total_students
                * 100,
                2,
            )
        else:
            eligible_rate = 0.0
            not_eligible_rate = 0.0
            insufficient_data_rate = 0.0

        failure_counter: Counter[str] = Counter()
        missing_field_counter: Counter[str] = Counter()

        for result in results:
            failure_counter.update(
                result.failed_conditions
            )

            missing_field_counter.update(
                result.missing_fields
            )

        top_failed_conditions = [
            {
                "condition": condition,
                "student_count": count,
                "rate": round(
                    count
                    / total_students
                    * 100,
                    2,
                )
                if total_students > 0
                else 0.0,
            }
            for condition, count
            in failure_counter.most_common(10)
        ]

        top_missing_fields = [
            {
                "field_name": field_name,
                "student_count": count,
                "rate": round(
                    count
                    / total_students
                    * 100,
                    2,
                )
                if total_students > 0
                else 0.0,
            }
            for field_name, count
            in missing_field_counter.most_common(10)
        ]

        return GraduationSummary(
            total_students=total_students,
            eligible_count=eligible_count,
            not_eligible_count=not_eligible_count,
            insufficient_data_count=(
                insufficient_data_count
            ),
            eligible_rate=eligible_rate,
            not_eligible_rate=(
                not_eligible_rate
            ),
            insufficient_data_rate=(
                insufficient_data_rate
            ),
            top_failed_conditions=(
                top_failed_conditions
            ),
            top_missing_fields=(
                top_missing_fields
            ),
        )