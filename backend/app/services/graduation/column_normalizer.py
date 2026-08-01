from __future__ import annotations

from app.services.common.base_column_normalizer import (
    BaseColumnNormalizer,
)


class GraduationColumnNormalizer(
    BaseColumnNormalizer
):
    """
    Chuẩn hóa tên cột dành riêng cho dữ liệu
    đăng ký xét tốt nghiệp.

    Tất cả tên cột đầu vào sẽ được ánh xạ về
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

        "accumulated_credits": {
            "accumulated_credits",
            "cumulative_credits",
            "earned_credits",
            "completed_credits",
            "total_credits",
            "credits",
            "credits_earned",
            "tin_chi",
            "so_tin_chi",
            "tong_tin_chi",
            "tin_chi_tich_luy",
            "so_tin_chi_tich_luy",
            "tong_tin_chi_tich_luy",
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

        "english_status": {
            "english_status",
            "english_certificate",
            "language_status",
            "foreign_language_status",
            "ngoai_ngu",
            "chuan_ngoai_ngu",
            "trang_thai_ngoai_ngu",
            "chung_chi_ngoai_ngu",
            "english_passed",
            "chuandau_ngoai_ngu",
            "chuan_dau_ra_ngoai_ngu",
        },

        "informatics_status": {
            "informatics_status",
            "computer_certificate",
            "it_certificate",
            "tin_hoc",
            "chuan_tin_hoc",
            "trang_thai_tin_hoc",
            "chung_chi_tin_hoc",
            "chuandau_tin_hoc",
            "chuan_dau_ra_tin_hoc",
        },

        "physical_education_status": {
            "physical_education_status",
            "physical_education",
            "pe_status",
            "gdtc",
            "giao_duc_the_chat",
            "trang_thai_gdtc",
        },

        "national_defense_status": {
            "national_defense_status",
            "national_defense",
            "defense_education_status",
            "gdqp",
            "giao_duc_quoc_phong",
            "trang_thai_gdqp",
            "chung_chi_gdqp_gddt",
            "chung_chi_gdqp_gdtc",
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

        "conduct_score": {
            "conduct_score",
            "training_score",
            "behavior_score",
            "diem_ren_luyen",
            "ren_luyen",
            "drl",
        },

        "discipline_status": {
            "discipline_status",
            "disciplinary_status",
            "discipline",
            "ky_luat",
            "trang_thai_ky_luat",
        },

        "graduation_project_status": {
            "graduation_project_status",
            "thesis_status",
            "capstone_status",
            "graduation_thesis_status",
            "khoa_luan",
            "do_an_tot_nghiep",
            "khoa_luan_tot_nghiep",
            "trang_thai_khoa_luan",
        },

        "application_status": {
            "application_status",
            "graduation_application_status",
            "registration_status",
            "trang_thai_dang_ky",
            "dang_ky_xet_tot_nghiep",
            "trang_thai_ho_so",
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