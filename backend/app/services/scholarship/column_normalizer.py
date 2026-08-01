from __future__ import annotations

from app.services.common.base_column_normalizer import (
    BaseColumnNormalizer,
)


class ScholarshipColumnNormalizer(
    BaseColumnNormalizer
):
    """
    Chuẩn hóa tên cột dành riêng cho dữ liệu
    xét học bổng sinh viên.

    Tất cả tên cột đầu vào được ánh xạ về
    một bộ tên chuẩn duy nhất.
    """

    COLUMN_ALIASES = {
        "student_id": {
            "student_id",
            "student_code",
            "student_number",
            "mssv",
            "ma_sv",
            "ma_sinh_vien",
            "masv",
            "ma_so_sinh_vien",
        },

        "student_name": {
            "student_name",
            "full_name",
            "fullname",
            "name",
            "ho_ten",
            "ho_va_ten",
            "ten_sinh_vien",
            "ho_ten_sinh_vien",
        },

        "gpa": {
            "gpa",
            "cpa",
            "average_score",
            "cumulative_gpa",
            "cumulative_average",
            "diem_trung_binh",
            "diem_trung_binh_tich_luy",
            "diem_tb_tich_luy",
            "diem_tich_luy",
            "dtb_tich_luy",
            "gpa_tich_luy",
        },

        "conduct_score": {
            "conduct_score",
            "training_score",
            "behavior_score",
            "diem_ren_luyen",
            "ren_luyen",
            "drl",
        },

        "failed_courses": {
            "failed_courses",
            "failed_subjects",
            "remaining_courses",
            "incomplete_courses",
            "no_mon",
            "so_mon_no",
            "mon_no",
            "hoc_phan_no",
            "so_hoc_phan_no",
            "hoc_phan_chua_dat",
            "so_hoc_phan_chua_dat",
            "mandatory_courses_remaining",
        },

        "tuition_status": {
            "tuition_status",
            "financial_status",
            "financial_obligation",
            "hoc_phi",
            "trang_thai_hoc_phi",
            "nghia_vu_tai_chinh",
            "cong_no",
            "no_hoc_phi",
        },

        "discipline_status": {
            "discipline_status",
            "disciplinary_status",
            "discipline",
            "ky_luat",
            "trang_thai_ky_luat",
            "tinh_trang_ky_luat",
        },

        "financial_difficulty": {
            "financial_difficulty",
            "financial_condition",
            "difficult_circumstances",
            "family_condition",
            "hoan_canh",
            "hoan_canh_kho_khan",
            "dieu_kien_kinh_te",
            "gia_dinh_kho_khan",
            "doi_tuong_uu_tien",
        },

        "registered_on_time": {
            "registered_on_time",
            "submitted_on_time",
            "application_on_time",
            "registration_status",
            "dang_ky_dung_han",
            "nop_ho_so_dung_han",
            "dang_ky_hoc_bong",
            "trang_thai_dang_ky",
        },

        "scholarship_type": {
            "scholarship_type",
            "type_of_scholarship",
            "scholarship_category",
            "loai_hoc_bong",
            "nhom_hoc_bong",
            "danh_muc_hoc_bong",
        },

        "scholarship_result": {
            "scholarship_result",
            "evaluation_result",
            "result",
            "ket_qua_hoc_bong",
            "ket_qua_xet_hoc_bong",
            "ket_qua",
        },

        "major": {
            "major",
            "program",
            "field_of_study",
            "nganh",
            "chuyen_nganh",
            "nganh_hoc",
        },

        "cohort": {
            "cohort",
            "course",
            "intake",
            "academic_cohort",
            "khoa",
            "nien_khoa",
            "khoa_hoc",
        },
    }