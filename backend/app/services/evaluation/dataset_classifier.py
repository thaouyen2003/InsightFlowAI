from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pandas as pd

from app.services.common.base_column_normalizer import (
    BaseColumnNormalizer,
)


@dataclass
class DatasetClassificationResult:
    category: str
    label: str
    confidence: float
    matched_columns: list[str]
    reasons: list[str]


class DatasetClassifier:
    """
    Nhận diện loại nghiệp vụ của dataset dựa trên
    tên cột đã chuẩn hóa.

    Giai đoạn đầu dùng rule-based classifier để:
    - chạy ổn định;
    - dễ kiểm tra;
    - không phụ thuộc LLM;
    - tránh tốn quota.

    Sau này có thể bổ sung LLM fallback.
    """

    CATEGORY_LABELS: ClassVar[dict[str, str]] = {
        "graduation": "Xét điều kiện tốt nghiệp",
        "scholarship": "Xét điều kiện học bổng",
        "admission": "Xét tuyển đầu vào",
        "academic_warning": "Cảnh báo học vụ",
        "general": "Phân tích dữ liệu tổng quát",
    }

    CATEGORY_SIGNATURES: ClassVar[
        dict[str, set[str]]
    ] = {
        "graduation": {
            "mssv",
            "ma_sinh_vien",
            "gpa",
            "cpa",
            "gpa_tich_luy",
            "tin_chi_tich_luy",
            "chuandau_ngoai_ngu",
            "chuan_dau_ra_ngoai_ngu",
            "chuandau_tin_hoc",
            "chuan_dau_ra_tin_hoc",
            "gdqp",
            "gdtc",
            "no_hoc_phi",
            "ky_luat",
        },

        "scholarship": {
            "mssv",
            "ma_sinh_vien",
            "gpa",
            "diem_trung_binh",
            "diem_ren_luyen",
            "so_tin_chi",
            "hoc_bong",
            "loai_hoc_bong",
            "hoan_canh",
            "ky_luat",
        },

        "admission": {
            "ma_ho_so",
            "so_bao_danh",
            "phuong_thuc_xet_tuyen",
            "diem_xet_tuyen",
            "diem_thi_thpt",
            "diem_hoc_ba",
            "diem_dgnl",
            "nguyen_vong",
            "nganh_dang_ky",
            "ket_qua_xet_tuyen",
        },

        "academic_warning": {
            "mssv",
            "gpa",
            "cpa",
            "tin_chi_dat",
            "tin_chi_no",
            "mon_no",
            "canh_bao_hoc_vu",
            "diem_ren_luyen",
        },
    }

    MINIMUM_MATCH_COUNT: ClassVar[int] = 2

    @classmethod
    def normalize_columns(
        cls,
        df: pd.DataFrame,
    ) -> set[str]:
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "df phải là pandas.DataFrame"
            )

        return {
            BaseColumnNormalizer.normalize_text(
                column
            )
            for column in df.columns
        }

    @classmethod
    def classify(
        cls,
        df: pd.DataFrame,
    ) -> DatasetClassificationResult:
        normalized_columns = (
            cls.normalize_columns(df)
        )

        scores: dict[str, int] = {}
        matches: dict[str, list[str]] = {}

        for category, signatures in (
            cls.CATEGORY_SIGNATURES.items()
        ):
            matched = sorted(
                normalized_columns
                & signatures
            )

            matches[category] = matched
            scores[category] = len(matched)

        best_category = max(
            scores,
            key=scores.get,
        )

        best_score = scores[best_category]

        if best_score < cls.MINIMUM_MATCH_COUNT:
            return DatasetClassificationResult(
                category="general",
                label=cls.CATEGORY_LABELS[
                    "general"
                ],
                confidence=0.0,
                matched_columns=[],
                reasons=[
                    "Không tìm thấy đủ cột đặc trưng "
                    "để xác định nghiệp vụ.",
                ],
            )

        signature_count = len(
            cls.CATEGORY_SIGNATURES[
                best_category
            ]
        )

        confidence = min(
            best_score / max(
                signature_count,
                1,
            ),
            1.0,
        )

        return DatasetClassificationResult(
            category=best_category,
            label=cls.CATEGORY_LABELS[
                best_category
            ],
            confidence=round(
                confidence,
                4,
            ),
            matched_columns=matches[
                best_category
            ],
            reasons=[
                (
                    "Nhận diện dựa trên các cột: "
                    + ", ".join(
                        matches[best_category]
                    )
                )
            ],
        )