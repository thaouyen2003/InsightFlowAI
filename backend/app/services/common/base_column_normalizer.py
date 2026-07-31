from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import ClassVar

import pandas as pd


@dataclass
class ColumnNormalizationReport:
    """
    Báo cáo kết quả chuẩn hóa tên cột.

    Thuộc tính:
    - original_columns: Các cột ban đầu.
    - normalized_columns: Các cột sau khi chuẩn hóa.
    - renamed_columns: Cột gốc và tên chuẩn tương ứng.
    - unrecognized_columns: Các cột chưa có trong alias.
    - duplicate_targets: Các tên chuẩn bị nhiều cột cùng ánh xạ tới.
    """

    original_columns: list[str] = field(
        default_factory=list,
    )

    normalized_columns: list[str] = field(
        default_factory=list,
    )

    renamed_columns: dict[str, str] = field(
        default_factory=dict,
    )

    unrecognized_columns: list[str] = field(
        default_factory=list,
    )

    duplicate_targets: dict[str, list[str]] = field(
        default_factory=dict,
    )

    @property
    def has_duplicates(self) -> bool:
        """
        Kiểm tra có xảy ra ánh xạ trùng cột hay không.
        """

        return bool(self.duplicate_targets)


class BaseColumnNormalizer:
    """
    Lớp cơ sở dùng chung để chuẩn hóa tên cột.

    Các module con chỉ cần khai báo COLUMN_ALIASES.

    Ví dụ:

    COLUMN_ALIASES = {
        "student_id": {
            "mssv",
            "ma_sinh_vien",
            "student_id",
        },
    }
    """

    COLUMN_ALIASES: ClassVar[
        dict[str, set[str]]
    ] = {}

    KEEP_UNRECOGNIZED_COLUMNS: ClassVar[
        bool
    ] = True

    @classmethod
    def normalize_text(
        cls,
        value: object,
    ) -> str:
        """
        Chuẩn hóa một chuỗi về dạng snake_case không dấu.

        Ví dụ:
        - "Mã Sinh Viên" -> "ma_sinh_vien"
        - "Điểm TB Tích Lũy" -> "diem_tb_tich_luy"
        - "Student-ID" -> "student_id"
        """

        if value is None:
            return ""

        text = str(value).strip().lower()

        # Xử lý riêng ký tự đ/Đ vì Unicode normalize
        # không tự chuyển đ thành d.
        text = text.replace("đ", "d")

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

        # Thay các ký tự không phải chữ hoặc số bằng "_".
        text = re.sub(
            r"[^a-z0-9]+",
            "_",
            text,
        )

        # Gộp nhiều dấu "_" liên tiếp.
        text = re.sub(
            r"_+",
            "_",
            text,
        )

        return text.strip("_")

    @classmethod
    def get_alias_lookup(
        cls,
    ) -> dict[str, str]:
        """
        Tạo bảng tra cứu:

        alias đã chuẩn hóa -> tên cột chuẩn.
        """

        lookup: dict[str, str] = {}

        for canonical_name, aliases in (
            cls.COLUMN_ALIASES.items()
        ):
            normalized_canonical = (
                cls.normalize_text(
                    canonical_name
                )
            )

            all_aliases = set(aliases)
            all_aliases.add(canonical_name)

            for alias in all_aliases:
                normalized_alias = (
                    cls.normalize_text(alias)
                )

                if not normalized_alias:
                    continue

                existing_target = lookup.get(
                    normalized_alias
                )

                if (
                    existing_target is not None
                    and existing_target
                    != normalized_canonical
                ):
                    raise ValueError(
                        "Alias bị khai báo trùng: "
                        f"'{alias}' đang cùng ánh xạ "
                        f"tới '{existing_target}' và "
                        f"'{normalized_canonical}'."
                    )

                lookup[
                    normalized_alias
                ] = normalized_canonical

        return lookup

    @classmethod
    def build_rename_map(
        cls,
        columns: list[object],
    ) -> tuple[
        dict[object, str],
        ColumnNormalizationReport,
    ]:
        """
        Tạo rename map và báo cáo chuẩn hóa.
        """

        alias_lookup = cls.get_alias_lookup()

        rename_map: dict[object, str] = {}

        recognized_columns: dict[
            str,
            list[str],
        ] = {}

        report = ColumnNormalizationReport(
            original_columns=[
                str(column)
                for column in columns
            ],
        )

        for column in columns:
            original_name = str(column)

            normalized_name = cls.normalize_text(
                original_name
            )

            canonical_name = alias_lookup.get(
                normalized_name
            )

            if canonical_name is not None:
                target_name = canonical_name

                report.renamed_columns[
                    original_name
                ] = target_name

                recognized_columns.setdefault(
                    target_name,
                    [],
                ).append(original_name)

            elif cls.KEEP_UNRECOGNIZED_COLUMNS:
                target_name = normalized_name

                report.unrecognized_columns.append(
                    original_name
                )

            else:
                target_name = original_name

                report.unrecognized_columns.append(
                    original_name
                )

            rename_map[column] = target_name

        report.duplicate_targets = {
            target_name: source_columns
            for target_name, source_columns
            in recognized_columns.items()
            if len(source_columns) > 1
        }

        report.normalized_columns = [
            rename_map[column]
            for column in columns
        ]

        return rename_map, report

    @classmethod
    def normalize(
        cls,
        df: pd.DataFrame,
        *,
        raise_on_duplicate: bool = True,
        return_report: bool = False,
    ) -> (
        pd.DataFrame
        | tuple[
            pd.DataFrame,
            ColumnNormalizationReport,
        ]
    ):
        """
        Chuẩn hóa tên cột của DataFrame.

        Tham số:
        - raise_on_duplicate:
          Nếu True, báo lỗi khi nhiều cột cùng ánh xạ
          về một tên chuẩn.

        - return_report:
          Nếu True, trả về cả DataFrame và báo cáo.
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "df phải là pandas.DataFrame"
            )

        result_df = df.copy()

        rename_map, report = (
            cls.build_rename_map(
                list(result_df.columns)
            )
        )

        if (
            raise_on_duplicate
            and report.has_duplicates
        ):
            duplicate_descriptions = []

            for (
                target_name,
                source_columns,
            ) in report.duplicate_targets.items():
                duplicate_descriptions.append(
                    f"{target_name}: "
                    + ", ".join(source_columns)
                )

            raise ValueError(
                "Phát hiện nhiều cột cùng ánh xạ "
                "về một tên chuẩn: "
                + "; ".join(
                    duplicate_descriptions
                )
            )

        result_df = result_df.rename(
            columns=rename_map
        )

        if return_report:
            return result_df, report

        return result_df