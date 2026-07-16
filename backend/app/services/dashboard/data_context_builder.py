from typing import Any

import pandas as pd

from app.services.semantic_analysis.column_analyzer import (
    ColumnAnalyzer,
)


class DataContextBuilder:
    """
    Xây dựng ngữ cảnh dữ liệu dùng chung cho toàn bộ dashboard.

    Data context giúp các service phía sau hiểu:
    - Cột nào là identifier
    - Cột nào là dimension
    - Cột nào là measure
    - Cột nào là datetime, currency, percentage...
    """

    def __init__(self):
        self.column_analyzer = ColumnAnalyzer()

    def build(
        self,
        df: pd.DataFrame,
    ) -> dict[str, Any]:
        columns = self.column_analyzer.analyze(df)

        identifiers = [
            column
            for column in columns
            if column["role"] == "identifier"
        ]

        dimensions = [
            column
            for column in columns
            if column["role"] == "dimension"
        ]

        measures = [
            column
            for column in columns
            if column["role"] == "measure"
        ]

        unsupported = [
            column
            for column in columns
            if column["role"] == "unsupported"
        ]

        datetime_columns = [
            column
            for column in dimensions
            if column["semantic_type"] == "datetime"
        ]

        categorical_columns = [
            column
            for column in dimensions
            if column["semantic_type"] in {
                "category",
                "geography",
                "boolean",
            }
        ]

        currency_columns = [
            column
            for column in measures
            if column["semantic_type"] == "currency"
        ]

        percentage_columns = [
            column
            for column in measures
            if column["semantic_type"] == "percentage"
        ]

        quantity_columns = [
            column
            for column in measures
            if column["semantic_type"] == "quantity"
        ]

        warnings = self._build_warnings(
            df=df,
            columns=columns,
            identifiers=identifiers,
            dimensions=dimensions,
            measures=measures,
        )

        return {
            "rows": int(len(df)),
            "column_count": int(len(df.columns)),
            "columns": columns,
            "identifiers": identifiers,
            "dimensions": dimensions,
            "measures": measures,
            "unsupported": unsupported,
            "datetime_columns": datetime_columns,
            "categorical_columns": categorical_columns,
            "currency_columns": currency_columns,
            "percentage_columns": percentage_columns,
            "quantity_columns": quantity_columns,
            "role_summary": {
                "identifiers": len(identifiers),
                "dimensions": len(dimensions),
                "measures": len(measures),
                "unsupported": len(unsupported),
            },
            "warnings": warnings,
        }

    def _build_warnings(
        self,
        df: pd.DataFrame,
        columns: list[dict[str, Any]],
        identifiers: list[dict[str, Any]],
        dimensions: list[dict[str, Any]],
        measures: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        warnings: list[dict[str, str]] = []

        if df.empty:
            warnings.append({
                "type": "empty_dataset",
                "message": "Dataset không có dòng dữ liệu.",
            })

        if not measures:
            warnings.append({
                "type": "no_measure",
                "message": (
                    "Không phát hiện measure phù hợp. "
                    "Dashboard có thể không tạo được KPI tổng hợp."
                ),
            })

        if not dimensions:
            warnings.append({
                "type": "no_dimension",
                "message": (
                    "Không phát hiện dimension phù hợp. "
                    "Dashboard có thể không tạo được biểu đồ phân nhóm."
                ),
            })

        if not any(
            column["semantic_type"] == "datetime"
            for column in columns
        ):
            warnings.append({
                "type": "no_datetime",
                "message": (
                    "Không phát hiện cột thời gian. "
                    "Dashboard sẽ không có biểu đồ xu hướng."
                ),
            })

        high_missing_columns = [
            column["name"]
            for column in columns
            if column["missing_percentage"] >= 50
        ]

        if high_missing_columns:
            warnings.append({
                "type": "high_missing_values",
                "message": (
                    "Các cột có ít nhất 50% dữ liệu thiếu: "
                    + ", ".join(high_missing_columns)
                ),
            })

        if identifiers and len(identifiers) == len(columns):
            warnings.append({
                "type": "identifier_only",
                "message": (
                    "Hầu hết cột được nhận diện là định danh. "
                    "Dữ liệu hiện tại chưa phù hợp để tổng hợp dashboard."
                ),
            })

        return warnings