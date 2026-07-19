import re
from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)



class ColumnAnalyzer:
    """
    Phân tích kiểu dữ liệu, ý nghĩa và vai trò của từng cột.

    Kết quả được dùng để:
    - Phân biệt identifier, dimension và measure
    - Làm sạch dữ liệu
    - Tạo KPI
    - Đề xuất biểu đồ
    """

    CATEGORY_KEYWORDS = {
    "category",
    "channel",
    "status",
    "method",
    "type",
    "segment",
    "department",
    "region",
    "rep",
    "representative",
    "name",
}

    ID_KEYWORDS = {
        "id",
        "uuid",
        "guid",
        "code",
        "key",
        "number",
        "no",
        "index",
        "identifier",
        "ma",
    }

    DATE_KEYWORDS = {
        "date",
        "time",
        "day",
        "month",
        "year",
        "created",
        "updated",
        "timestamp",
        "datetime",
        "ngay",
        "thang",
        "nam",
    }

    CURRENCY_KEYWORDS = {
        "revenue",
        "sales",
        "amount",
        "price",
        "cost",
        "profit",
        "income",
        "expense",
        "salary",
        "total",
        "subtotal",
        "payment",
        "budget",
        "doanh_thu",
        "chi_phi",
        "loi_nhuan",
        "gia",
        "tien",
    }

    PERCENTAGE_KEYWORDS = {
        "percent",
        "percentage",
        "rate",
        "ratio",
        "discount",
        "margin",
        "growth",
        "conversion",
        "ty_le",
        "phan_tram",
    }

    QUANTITY_KEYWORDS = {
        "quantity",
        "qty",
        "count",
        "volume",
        "units",
        "stock",
        "inventory",
        "orders",
        "customers",
        "so_luong",
    }

    GEOGRAPHY_KEYWORDS = {
        "country",
        "city",
        "province",
        "district",
        "region",
        "state",
        "location",
        "address",
        "area",
        "quoc_gia",
        "thanh_pho",
        "tinh",
        "quan",
        "khu_vuc",
    }

    BOOLEAN_VALUES = {
        "true",
        "false",
        "yes",
        "no",
        "y",
        "n",
        "1",
        "0",
        "active",
        "inactive",
        "enabled",
        "disabled",
        "có",
        "không",
        "co",
        "khong",
    }

    def analyze(
        self,
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        """
        Phân tích toàn bộ các cột trong DataFrame.
        """

        results: list[dict[str, Any]] = []

        for column_name in df.columns:
            series = df[column_name]

            metadata = self._analyze_column(
                column_name=str(column_name),
                series=series,
                total_rows=len(df),
            )

            results.append(metadata)

        return results

    def _analyze_column(
        self,
        column_name: str,
        series: pd.Series,
        total_rows: int,
    ) -> dict[str, Any]:
        clean_series = series.dropna()
        normalized_name = self._normalize_name(column_name)

        unique_count = int(clean_series.nunique())
        missing_count = int(series.isna().sum())

        if total_rows > 0:
            missing_percentage = round(
                missing_count / total_rows * 100,
                2,
            )
        else:
            missing_percentage = 0

        inferred_type = self._infer_type(
            normalized_name=normalized_name,
            series=series,
        )

        semantic_type = self._infer_semantic_type(
            normalized_name=normalized_name,
            inferred_type=inferred_type,
            unique_count=unique_count,
            total_rows=total_rows,
        )

        role = self._infer_role(
            normalized_name=normalized_name,
            inferred_type=inferred_type,
            semantic_type=semantic_type,
            unique_count=unique_count,
            total_rows=total_rows,
        )

        aggregation = self._infer_aggregation(
            semantic_type=semantic_type,
            role=role,
        )

        confidence = self._calculate_confidence(
            normalized_name=normalized_name,
            inferred_type=inferred_type,
            semantic_type=semantic_type,
        )

        return {
            "name": column_name,
            "normalized_name": normalized_name,
            "original_dtype": str(series.dtype),
            "inferred_type": inferred_type,
            "semantic_type": semantic_type,
            "role": role,
            "aggregation": aggregation,
            "unique_count": unique_count,
            "missing_count": missing_count,
            "missing_percentage": missing_percentage,
            "confidence": confidence,
            "sample": self._get_sample(clean_series),
        }

    def _normalize_name(
        self,
        column_name: str,
    ) -> str:
        normalized = column_name.strip().lower()

        normalized = re.sub(
            r"[^a-zA-Z0-9À-ỹ]+",
            "_",
            normalized,
        )

        normalized = re.sub(
            r"_+",
            "_",
            normalized,
        )

        return normalized.strip("_")

    def _infer_type(
        self,
        normalized_name: str,
        series: pd.Series,
    ) -> str:
        if is_bool_dtype(series):
            return "boolean"

        if is_datetime64_any_dtype(series):
            return "datetime"

        if is_numeric_dtype(series):
            return "numeric"

        clean_series = series.dropna()

        if clean_series.empty:
            return "unknown"

        if self._looks_like_boolean(clean_series):
            return "boolean"

        if self._looks_like_datetime(
            normalized_name=normalized_name,
            series=clean_series,
        ):
            return "datetime"

        if self._looks_like_numeric(clean_series):
            return "numeric"

        return "text"

    def _infer_semantic_type(
        self,
        normalized_name: str,
        inferred_type: str,
        unique_count: int,
        total_rows: int,
    ) -> str:
        tokens = set(normalized_name.split("_"))

        if self._contains_keyword(
            tokens,
            self.CURRENCY_KEYWORDS,
        ):
            return "currency"

        if self._contains_keyword(
            tokens,
            self.PERCENTAGE_KEYWORDS,
        ):
            return "percentage"

        if self._contains_keyword(
            tokens,
            self.QUANTITY_KEYWORDS,
        ):
            return "quantity"

        if self._contains_keyword(
            tokens,
            self.DATE_KEYWORDS,
        ):
            return "datetime"

        if self._contains_keyword(
            tokens,
            self.GEOGRAPHY_KEYWORDS,
        ):
            return "geography"

        if self._contains_keyword(
            tokens,
            self.ID_KEYWORDS,
        ):
            return "identifier"

        if inferred_type == "boolean":
            return "boolean"

        if inferred_type == "datetime":
            return "datetime"

        if inferred_type == "numeric":
            if self._is_probable_identifier(
                normalized_name=normalized_name,
                unique_count=unique_count,
                total_rows=total_rows,
            ):
                return "identifier"

            return "measure"

        if inferred_type == "text":
            if total_rows == 0:
                return "text"

            unique_ratio = unique_count / total_rows

            if unique_count <= 30 or unique_ratio <= 0.2:
                return "category"

            return "text"

        return "unknown"

    def _infer_role(
        self,
        normalized_name: str,
        inferred_type: str,
        semantic_type: str,
        unique_count: int,
        total_rows: int,
    ) -> str:
        if semantic_type == "identifier":
            return "identifier"

        if semantic_type in {
            "currency",
            "percentage",
            "quantity",
            "measure",
        }:
            return "measure"

        if semantic_type in {
            "category",
            "datetime",
            "geography",
            "boolean",
        }:
            return "dimension"

        if inferred_type == "numeric":
            if self._is_probable_identifier(
                normalized_name=normalized_name,
                unique_count=unique_count,
                total_rows=total_rows,
            ):
                return "identifier"

            return "measure"

        if inferred_type == "text":
            return "dimension"

        return "unsupported"

    def _infer_aggregation(
        self,
        semantic_type: str,
        role: str,
    ) -> str | None:
        if role != "measure":
            return None

        if semantic_type == "percentage":
            return "mean"

        if semantic_type in {
            "currency",
            "quantity",
            "measure",
        }:
            return "sum"

        return "sum"

    def _looks_like_boolean(
        self,
        series: pd.Series,
    ) -> bool:
        values = {
            str(value).strip().lower()
            for value in series.unique()[:20]
        }

        return bool(values) and values.issubset(
            self.BOOLEAN_VALUES
        )

    def _looks_like_datetime(
        self,
        normalized_name: str,
        series: pd.Series,
    ) -> bool:
        tokens = set(normalized_name.split("_"))

        has_date_keyword = self._contains_keyword(
            tokens,
            self.DATE_KEYWORDS,
        )

        sample = series.astype(str).head(100)

        try:
            converted = pd.to_datetime(
                sample,
                errors="coerce",
            )

            success_ratio = float(
                converted.notna().mean()
            )
        except Exception:
            return False

        if has_date_keyword and success_ratio >= 0.5:
            return True

        return success_ratio >= 0.85

    def _looks_like_numeric(
        self,
        series: pd.Series,
    ) -> bool:
        sample = series.astype(str).head(200)

        normalized = (
            sample
            .str.strip()
            .str.replace(
                r"[₫$€£¥]",
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
            .str.replace(
                r"\s+",
                "",
                regex=True,
            )
        )

        converted = pd.to_numeric(
            normalized,
            errors="coerce",
        )

        success_ratio = float(
            converted.notna().mean()
        )

        return success_ratio >= 0.8

    def _is_probable_identifier(
        self,
        normalized_name: str,
        unique_count: int,
        total_rows: int,
    ) -> bool:
        tokens = set(normalized_name.split("_"))

        if self._contains_keyword(
            tokens,
            self.ID_KEYWORDS,
        ):
            return True

        if total_rows == 0:
            return False

        unique_ratio = unique_count / total_rows

        return unique_ratio >= 0.98

    def _contains_keyword(
        self,
        tokens: set[str],
        keywords: set[str],
    ) -> bool:
        return bool(
            tokens.intersection(keywords)
        )

    def _calculate_confidence(
        self,
        normalized_name: str,
        inferred_type: str,
        semantic_type: str,
    ) -> float:
        tokens = set(normalized_name.split("_"))

        keyword_groups = [
            self.ID_KEYWORDS,
            self.DATE_KEYWORDS,
            self.CURRENCY_KEYWORDS,
            self.PERCENTAGE_KEYWORDS,
            self.QUANTITY_KEYWORDS,
            self.GEOGRAPHY_KEYWORDS,
        ]

        matched_by_name = any(
            self._contains_keyword(
                tokens,
                keyword_group,
            )
            for keyword_group in keyword_groups
        )

        if matched_by_name:
            return 0.95

        if semantic_type in {
            "boolean",
            "datetime",
            "measure",
            "category",
        }:
            return 0.85

        if inferred_type == "unknown":
            return 0.3

        return 0.7

    def _get_sample(
        self,
        series: pd.Series,
        limit: int = 5,
    ) -> list[Any]:
        sample = series.head(limit).tolist()

        return [
            self._make_json_safe(value)
            for value in sample
        ]

    def _make_json_safe(
        self,
        value: Any,
    ) -> Any:
        if isinstance(value, pd.Timestamp):
            return value.isoformat()

        if hasattr(value, "item"):
            return value.item()

        return value