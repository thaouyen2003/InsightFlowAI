import re
from typing import Any

import pandas as pd


class DataCleaner:
    """
    Làm sạch DataFrame dựa trên metadata semantic.

    Nguyên tắc:
    - Không làm thay đổi cột identifier ngoài việc chuẩn hóa chuỗi.
    - Không làm mất số 0 ở đầu của mã.
    - Không ép kiểu nếu tỷ lệ chuyển đổi quá thấp.
    - Không để lỗi một cột làm hỏng toàn bộ DataFrame.
    - Luôn trả về danh sách warning để theo dõi.
    """

    NULL_VALUES = {
        "",
        "null",
        "none",
        "nan",
        "n/a",
        "na",
        "unknown",
        "undefined",
        "-",
        "--",
    }

    TRUE_VALUES = {
        "true",
        "yes",
        "y",
        "1",
        "active",
        "enabled",
        "on",
        "có",
        "co",
        "đúng",
        "dung",
    }

    FALSE_VALUES = {
        "false",
        "no",
        "n",
        "0",
        "inactive",
        "disabled",
        "off",
        "không",
        "khong",
        "sai",
    }

    MIN_CONVERSION_RATE = 0.6

    def clean(
        self,
        df: pd.DataFrame,
        columns_metadata: list[dict[str, Any]],
    ) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
        """
        Làm sạch toàn bộ DataFrame.

        Trả về:
        - DataFrame đã làm sạch.
        - Danh sách warnings/conversion logs.
        """

        cleaned_df = df.copy()

        warnings: list[dict[str, Any]] = []

        metadata_map = {
            item["name"]: item
            for item in columns_metadata
        }

        for column_name in cleaned_df.columns:
            column_name_as_string = str(column_name)

            metadata = metadata_map.get(
                column_name_as_string
            )

            if metadata is None:
                warnings.append({
                    "column": column_name_as_string,
                    "type": "metadata_missing",
                    "message": (
                        "Không tìm thấy metadata semantic "
                        "cho cột này."
                    ),
                })

                continue

            try:
                series = cleaned_df[column_name]

                series = self._normalize_missing_values(
                    series
                )

                role = metadata.get("role")
                semantic_type = metadata.get(
                    "semantic_type"
                )
                inferred_type = metadata.get(
                    "inferred_type"
                )

                if role == "identifier":
                    cleaned_df[column_name] = (
                        self._clean_identifier(series)
                    )

                    warnings.append({
                        "column": column_name_as_string,
                        "type": "identifier_preserved",
                        "message": (
                            "Cột identifier được giữ dưới "
                            "dạng chuỗi để tránh mất dữ liệu."
                        ),
                    })

                    continue

                if semantic_type == "datetime":
                    cleaned_series, result = (
                        self._clean_datetime(series)
                    )

                    cleaned_df[column_name] = (
                        cleaned_series
                    )

                    warnings.append({
                        "column": column_name_as_string,
                        **result,
                    })

                    continue

                if semantic_type == "percentage":
                    cleaned_series, result = (
                        self._clean_percentage(series)
                    )

                    cleaned_df[column_name] = (
                        cleaned_series
                    )

                    warnings.append({
                        "column": column_name_as_string,
                        **result,
                    })

                    continue

                if semantic_type == "boolean":
                    cleaned_series, result = (
                        self._clean_boolean(series)
                    )

                    cleaned_df[column_name] = (
                        cleaned_series
                    )

                    warnings.append({
                        "column": column_name_as_string,
                        **result,
                    })

                    continue

                if (
                    semantic_type
                    in {
                        "currency",
                        "quantity",
                        "measure",
                    }
                    or inferred_type == "numeric"
                ):
                    cleaned_series, result = (
                        self._clean_numeric(series)
                    )

                    cleaned_df[column_name] = (
                        cleaned_series
                    )

                    warnings.append({
                        "column": column_name_as_string,
                        **result,
                    })

                    continue

                if semantic_type in {
                    "category",
                    "geography",
                    "text",
                }:
                    cleaned_df[column_name] = (
                        self._clean_text(series)
                    )

                    continue

                cleaned_df[column_name] = series

            except Exception as error:
                warnings.append({
                    "column": column_name_as_string,
                    "type": "cleaning_failed",
                    "message": (
                        "Không thể làm sạch cột: "
                        f"{str(error)}"
                    ),
                })

        return cleaned_df, warnings

    def _normalize_missing_values(
        self,
        series: pd.Series,
    ) -> pd.Series:
        """
        Chuẩn hóa các chuỗi biểu diễn missing value
        thành pd.NA.
        """

        if pd.api.types.is_numeric_dtype(series):
            return series

        def normalize(value: Any) -> Any:
            if pd.isna(value):
                return pd.NA

            normalized = str(value).strip()

            if normalized.lower() in self.NULL_VALUES:
                return pd.NA

            return value

        return series.map(normalize)

    def _clean_identifier(
        self,
        series: pd.Series,
    ) -> pd.Series:
        """
        Giữ identifier dưới dạng chuỗi.

        Ví dụ:
        00123 giữ nguyên thành "00123".
        123.0 có thể được chuẩn hóa thành "123".
        """

        def normalize(value: Any) -> Any:
            if pd.isna(value):
                return pd.NA

            value_as_string = str(value).strip()

            if re.fullmatch(
                r"\d+\.0",
                value_as_string,
            ):
                value_as_string = (
                    value_as_string[:-2]
                )

            return value_as_string

        return series.map(normalize).astype("string")

    def _clean_numeric(
        self,
        series: pd.Series,
    ) -> tuple[pd.Series, dict[str, Any]]:
        """
        Chuyển numeric dạng text thành numeric.

        Ví dụ:
        "1,200,000" → 1200000
        "$450" → 450
        "1 500" → 1500
        """

        if pd.api.types.is_numeric_dtype(series):
            return series, {
                "type": "numeric_unchanged",
                "message": (
                    "Cột đã có kiểu numeric, "
                    "không cần chuyển đổi."
                ),
                "success_rate": 1.0,
            }

        original_non_null = int(
            series.notna().sum()
        )

        normalized = (
            series.astype("string")
            .str.strip()
            .str.replace(
                r"[₫$€£¥]",
                "",
                regex=True,
            )
            .str.replace(
                r"\s+",
                "",
                regex=True,
            )
            .str.replace(
                ",",
                "",
                regex=False,
            )
            .str.replace(
                "%",
                "",
                regex=False,
            )
        )

        converted = pd.to_numeric(
            normalized,
            errors="coerce",
        )

        converted_non_null = int(
            converted.notna().sum()
        )

        success_rate = self._calculate_success_rate(
            original_non_null=original_non_null,
            converted_non_null=converted_non_null,
        )

        if success_rate < self.MIN_CONVERSION_RATE:
            return series, {
                "type": "numeric_conversion_skipped",
                "message": (
                    "Tỷ lệ chuyển đổi numeric quá thấp, "
                    "giữ nguyên dữ liệu ban đầu."
                ),
                "success_rate": success_rate,
            }

        return converted, {
            "type": "numeric_converted",
            "message": (
                "Đã chuyển cột sang kiểu numeric."
            ),
            "success_rate": success_rate,
        }

    def _clean_percentage(
        self,
        series: pd.Series,
    ) -> tuple[pd.Series, dict[str, Any]]:
        """
        Chuyển percentage thành numeric.

        Quy ước hiện tại:
        "20%" → 20.0

        Chưa chia cho 100 để frontend dễ hiển thị.
        """

        original_non_null = int(
            series.notna().sum()
        )

        normalized = (
            series.astype("string")
            .str.strip()
            .str.replace(
                "%",
                "",
                regex=False,
            )
            .str.replace(
                r"\s+",
                "",
                regex=True,
            )
            .str.replace(
                ",",
                ".",
                regex=False,
            )
        )

        converted = pd.to_numeric(
            normalized,
            errors="coerce",
        )

        converted_non_null = int(
            converted.notna().sum()
        )

        success_rate = self._calculate_success_rate(
            original_non_null=original_non_null,
            converted_non_null=converted_non_null,
        )

        if success_rate < self.MIN_CONVERSION_RATE:
            return series, {
                "type": "percentage_conversion_skipped",
                "message": (
                    "Tỷ lệ chuyển đổi phần trăm quá thấp, "
                    "giữ nguyên dữ liệu ban đầu."
                ),
                "success_rate": success_rate,
            }

        return converted, {
            "type": "percentage_converted",
            "message": (
                "Đã chuyển phần trăm sang numeric. "
                "Ví dụ 20% được lưu thành 20.0."
            ),
            "success_rate": success_rate,
        }

    def _clean_datetime(
        self,
        series: pd.Series,
    ) -> tuple[pd.Series, dict[str, Any]]:
        """
        Chuyển dữ liệu ngày tháng dạng text
        thành datetime.
        """

        if pd.api.types.is_datetime64_any_dtype(
            series
        ):
            return series, {
                "type": "datetime_unchanged",
                "message": (
                    "Cột đã có kiểu datetime, "
                    "không cần chuyển đổi."
                ),
                "success_rate": 1.0,
            }

        original_non_null = int(
            series.notna().sum()
        )

        converted = pd.to_datetime(
            series,
            errors="coerce",
            dayfirst=True,
        )

        converted_non_null = int(
            converted.notna().sum()
        )

        success_rate = self._calculate_success_rate(
            original_non_null=original_non_null,
            converted_non_null=converted_non_null,
        )

        if success_rate < self.MIN_CONVERSION_RATE:
            return series, {
                "type": "datetime_conversion_skipped",
                "message": (
                    "Tỷ lệ chuyển đổi ngày tháng quá thấp, "
                    "giữ nguyên dữ liệu ban đầu."
                ),
                "success_rate": success_rate,
            }

        return converted, {
            "type": "datetime_converted",
            "message": (
                "Đã chuyển cột sang kiểu datetime."
            ),
            "success_rate": success_rate,
        }

    def _clean_boolean(
        self,
        series: pd.Series,
    ) -> tuple[pd.Series, dict[str, Any]]:
        """
        Chuẩn hóa boolean.

        Ví dụ:
        YES → True
        NO → False
        """

        if pd.api.types.is_bool_dtype(series):
            return series, {
                "type": "boolean_unchanged",
                "message": (
                    "Cột đã có kiểu boolean, "
                    "không cần chuyển đổi."
                ),
                "success_rate": 1.0,
            }

        original_non_null = int(
            series.notna().sum()
        )

        def convert(value: Any) -> Any:
            if pd.isna(value):
                return pd.NA

            normalized = str(value).strip().lower()

            if normalized in self.TRUE_VALUES:
                return True

            if normalized in self.FALSE_VALUES:
                return False

            return pd.NA

        converted = (
            series
            .map(convert)
            .astype("boolean")
        )

        converted_non_null = int(
            converted.notna().sum()
        )

        success_rate = self._calculate_success_rate(
            original_non_null=original_non_null,
            converted_non_null=converted_non_null,
        )

        if success_rate < self.MIN_CONVERSION_RATE:
            return series, {
                "type": "boolean_conversion_skipped",
                "message": (
                    "Tỷ lệ chuyển đổi boolean quá thấp, "
                    "giữ nguyên dữ liệu ban đầu."
                ),
                "success_rate": success_rate,
            }

        return converted, {
            "type": "boolean_converted",
            "message": (
                "Đã chuyển cột sang kiểu boolean."
            ),
            "success_rate": success_rate,
        }

    def _clean_text(
        self,
        series: pd.Series,
    ) -> pd.Series:
        """
        Chuẩn hóa khoảng trắng của text/category.
        """

        def normalize(value: Any) -> Any:
            if pd.isna(value):
                return pd.NA

            normalized = re.sub(
                r"\s+",
                " ",
                str(value).strip(),
            )

            return normalized

        return series.map(normalize).astype("string")

    def _calculate_success_rate(
        self,
        original_non_null: int,
        converted_non_null: int,
    ) -> float:
        if original_non_null == 0:
            return 0.0

        return round(
            converted_non_null / original_non_null,
            4,
        )