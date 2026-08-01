from __future__ import annotations


class GraduationRuleSchema:
    """
    Danh sách trường dữ liệu mà Rule Engine
    được phép sử dụng.
    """

    SUPPORTED_FIELDS = {
        "gpa",
        "accumulated_credits",
        "failed_courses",
        "english_status",
        "informatics_status",
        "physical_education_status",
        "national_defense_status",
        "tuition_status",
        "conduct_score",
        "discipline_status",
        "graduation_project_status",
    }

    FIELD_DESCRIPTIONS = {
        "gpa": (
            "Điểm trung bình tích lũy của sinh viên"
        ),
        "accumulated_credits": (
            "Tổng số tín chỉ sinh viên đã tích lũy"
        ),
        "failed_courses": (
            "Số học phần chưa đạt hoặc còn nợ"
        ),
        "english_status": (
            "Trạng thái đạt chuẩn ngoại ngữ"
        ),
        "informatics_status": (
            "Trạng thái đạt chuẩn tin học"
        ),
        "physical_education_status": (
            "Trạng thái hoàn thành giáo dục thể chất"
        ),
        "national_defense_status": (
            "Trạng thái hoàn thành giáo dục quốc phòng"
        ),
        "tuition_status": (
            "Trạng thái hoàn thành nghĩa vụ tài chính"
        ),
        "conduct_score": (
            "Điểm rèn luyện"
        ),
        "discipline_status": (
            "Tình trạng kỷ luật"
        ),
        "graduation_project_status": (
            "Trạng thái khóa luận hoặc đồ án tốt nghiệp"
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