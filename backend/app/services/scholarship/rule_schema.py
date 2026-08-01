from __future__ import annotations


class ScholarshipRuleSchema:
    """
    Danh sách trường dữ liệu mà Rule Engine
    được phép sử dụng khi xét học bổng.
    """

    SUPPORTED_FIELDS = {
        "gpa",
        "conduct_score",
        "failed_courses",
        "tuition_status",
        "discipline_status",
        "financial_difficulty",
        "registered_on_time",
    }

    FIELD_DESCRIPTIONS = {
        "gpa": (
            "Điểm trung bình tích lũy"
        ),
        "conduct_score": (
            "Điểm rèn luyện"
        ),
        "failed_courses": (
            "Số học phần còn nợ"
        ),
        "tuition_status": (
            "Trạng thái hoàn thành học phí"
        ),
        "discipline_status": (
            "Tình trạng kỷ luật"
        ),
        "financial_difficulty": (
            "Hoàn cảnh khó khăn"
        ),
        "registered_on_time": (
            "Đăng ký đúng thời hạn"
        ),
    }

    @classmethod
    def is_supported(
        cls,
        field_name: str,
    ) -> bool:
        return (
            field_name
            in cls.SUPPORTED_FIELDS
        )