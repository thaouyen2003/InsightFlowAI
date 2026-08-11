from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ScholarshipValidationResult:
    """
    Kết quả kiểm tra dữ liệu xét học bổng.
    """

    is_valid: bool

    missing_required_columns: list[str] = field(
        default_factory=list,
    )

    optional_columns_missing: list[str] = field(
        default_factory=list,
    )

    duplicated_student_ids: list[str] = field(
        default_factory=list,
    )

    empty_student_ids: int = 0
    empty_student_names: int = 0

    warnings: list[str] = field(
        default_factory=list,
    )


class ScholarshipDataValidator:
    """
    Kiểm tra cấu trúc và chất lượng dữ liệu đầu vào
    phục vụ đánh giá học bổng.

    Các cột bắt buộc không được viết cứng hoàn toàn
    trong validator mà được truyền từ ScholarshipRuleSet.
    """

    IDENTITY_COLUMNS = {
        "student_id",
        "student_name",
    }

    KNOWN_EVALUATION_COLUMNS = {
        "gpa",
        "conduct_score",
        "failed_courses",
        "tuition_status",
        "discipline_status",
        "financial_difficulty",
        "registered_on_time",
        "scholarship_type",
        "scholarship_result",
    }

    @classmethod
    def validate(
        cls,
        df: pd.DataFrame,
        *,
        required_rule_fields: list[str] | None = None,
    ) -> ScholarshipValidationResult:
        """
        Kiểm tra DataFrame sau khi tên cột đã được
        ScholarshipColumnNormalizer chuẩn hóa.

        required_rule_fields được lấy từ bộ luật
        học bổng đang được sử dụng.
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "df phải là pandas.DataFrame"
            )

        if df.empty:
            return ScholarshipValidationResult(
                is_valid=False,
                warnings=[
                    "File không có dữ liệu sinh viên."
                ],
            )

        current_columns = set(df.columns)

        required_columns = set(
            cls.IDENTITY_COLUMNS
        )

        if required_rule_fields:
            required_columns.update(
                field_name
                for field_name
                in required_rule_fields
                if field_name
            )

        missing_required_columns = sorted(
            required_columns
            - current_columns
        )

        optional_columns = (
            cls.KNOWN_EVALUATION_COLUMNS
            - required_columns
        )

        optional_columns_missing = sorted(
            optional_columns
            - current_columns
        )

        duplicated_student_ids: list[str] = []

        empty_student_ids = 0
        empty_student_names = 0

        if "student_id" in df.columns:
            student_id_series = (
                df["student_id"]
                .astype("string")
                .str.strip()
            )

            empty_student_ids = int(
                student_id_series.isna().sum()
                + student_id_series.eq("").sum()
            )

            duplicate_mask = (
                student_id_series.notna()
                & student_id_series.ne("")
                & student_id_series.duplicated(
                    keep=False
                )
            )

            duplicated_student_ids = sorted(
                student_id_series[
                    duplicate_mask
                ]
                .dropna()
                .unique()
                .tolist()
            )

        if "student_name" in df.columns:
            student_name_series = (
                df["student_name"]
                .astype("string")
                .str.strip()
            )

            empty_student_names = int(
                student_name_series.isna().sum()
                + student_name_series.eq("").sum()
            )

        warnings: list[str] = []

        if optional_columns_missing:
            warnings.append(
                "Một số cột mở rộng không có trong "
                "dữ liệu. Các cột này không thuộc bộ "
                "luật bắt buộc hiện tại nên hệ thống "
                "vẫn có thể đánh giá."
            )

        if duplicated_student_ids:
            warnings.append(
                "Phát hiện mã sinh viên bị trùng."
            )

        if empty_student_ids > 0:
            warnings.append(
                f"Có {empty_student_ids} dòng "
                "không có mã sinh viên."
            )

        if empty_student_names > 0:
            warnings.append(
                f"Có {empty_student_names} dòng "
                "không có họ tên sinh viên."
            )

        is_valid = (
            not missing_required_columns
            and empty_student_ids == 0
            and not duplicated_student_ids
        )

        return ScholarshipValidationResult(
            is_valid=is_valid,
            missing_required_columns=(
                missing_required_columns
            ),
            optional_columns_missing=(
                optional_columns_missing
            ),
            duplicated_student_ids=(
                duplicated_student_ids
            ),
            empty_student_ids=empty_student_ids,
            empty_student_names=empty_student_names,
            warnings=warnings,
        )