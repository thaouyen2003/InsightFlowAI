from collections.abc import Iterable

from app.services.insight.insight_models import (
    InsightObject,
    InsightSeverity,
)


class InsightPipeline:
    """
    Xử lý và chuẩn hóa các InsightObject được tạo ra
    từ nhiều detector khác nhau.

    Pipeline hiện tại thực hiện:

    1. Loại insight không hợp lệ
    2. Loại insight trùng lặp
    3. Sắp xếp theo mức độ nghiêm trọng
    4. Giới hạn số insight trả về
    """

    DEFAULT_MAX_INSIGHTS = 20

    SEVERITY_PRIORITY = {
        InsightSeverity.CRITICAL: 4,
        InsightSeverity.HIGH: 3,
        InsightSeverity.MEDIUM: 2,
        InsightSeverity.LOW: 1,
    }

    def __init__(
        self,
        max_insights: int = DEFAULT_MAX_INSIGHTS,
    ) -> None:
        if max_insights <= 0:
            raise ValueError(
                "max_insights phải lớn hơn 0"
            )

        self.max_insights = max_insights

    def process(
        self,
        insights: Iterable[InsightObject],
    ) -> list[InsightObject]:
        """
        Chạy toàn bộ quá trình xử lý insight.
        """

        insight_list = list(insights)

        insight_list = self._remove_invalid_insights(
            insight_list
        )

        insight_list = self._remove_duplicate_insights(
            insight_list
        )

        insight_list = self._sort_by_priority(
            insight_list
        )

        return insight_list[
            : self.max_insights
        ]

    def _remove_invalid_insights(
        self,
        insights: list[InsightObject],
    ) -> list[InsightObject]:
        """
        Loại các insight thiếu thông tin cơ bản.
        """

        valid_insights: list[InsightObject] = []

        for insight in insights:
            if not insight.id:
                continue

            if not insight.title:
                continue

            if not insight.description:
                continue

            valid_insights.append(insight)

        return valid_insights

    def _remove_duplicate_insights(
        self,
        insights: list[InsightObject],
    ) -> list[InsightObject]:
        """
        Loại insight bị trùng ID.

        Nếu hai insight có cùng ID, giữ insight
        có severity cao hơn.
        """

        unique_insights: dict[
            str,
            InsightObject,
        ] = {}

        for insight in insights:
            current = unique_insights.get(
                insight.id
            )

            if current is None:
                unique_insights[
                    insight.id
                ] = insight
                continue

            current_priority = (
                self._get_severity_priority(
                    current.severity
                )
            )

            new_priority = (
                self._get_severity_priority(
                    insight.severity
                )
            )

            if new_priority > current_priority:
                unique_insights[
                    insight.id
                ] = insight

        return list(
            unique_insights.values()
        )

    def _sort_by_priority(
        self,
        insights: list[InsightObject],
    ) -> list[InsightObject]:
        """
        Sắp xếp insight theo severity giảm dần.

        Nếu cùng severity, insight có giá trị
        metric lớn hơn sẽ được ưu tiên trước.
        """

        return sorted(
            insights,
            key=self._build_sort_key,
            reverse=True,
        )

    def _build_sort_key(
        self,
        insight: InsightObject,
    ) -> tuple[int, float]:
        severity_priority = (
            self._get_severity_priority(
                insight.severity
            )
        )

        numeric_value = (
            float(insight.value)
            if isinstance(
                insight.value,
                (int, float),
            )
            else 0.0
        )

        return (
            severity_priority,
            numeric_value,
        )

    def _get_severity_priority(
        self,
        severity: InsightSeverity,
    ) -> int:
        return self.SEVERITY_PRIORITY.get(
            severity,
            0,
        )