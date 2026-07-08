"""
Schema Analyzer

Nhiệm vụ:
- Phân tích toàn bộ DataFrame
- Gọi ColumnProfiler cho từng cột
- Tạo Dataset Summary
- Trả về SchemaAnalysisResult
"""

import pandas as pd

from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
)

from app.services.schema.profiler import ColumnProfiler
from app.services.schema.models import (
    DatasetSummary,
    SchemaAnalysisResult,
)


class SchemaAnalyzer:

    def __init__(self):
        """
        Khởi tạo Profiler.
        """
        self.profiler = ColumnProfiler()

    def analyze(
        self,
        df: pd.DataFrame,
    ) -> SchemaAnalysisResult:
        """
        Phân tích toàn bộ DataFrame.
        """

        schema = []

        numeric_columns = 0
        categorical_columns = 0
        datetime_columns = 0

        # =====================================================
        # Phân tích từng cột
        # =====================================================

        for column in df.columns:

            profile = self.profiler.profile(df, column)

            schema.append(profile)

            if is_numeric_dtype(df[column]):
                numeric_columns += 1

            elif is_datetime64_any_dtype(df[column]):
                datetime_columns += 1

            else:
                categorical_columns += 1

        # =====================================================
        # Dataset Summary
        # =====================================================

        summary = DatasetSummary(

            rows=len(df),

            columns=len(df.columns),

            numeric_columns=numeric_columns,

            categorical_columns=categorical_columns,

            datetime_columns=datetime_columns,

            missing_cells=int(df.isna().sum().sum()),
        )

        # =====================================================
        # Trả kết quả
        # =====================================================

        return SchemaAnalysisResult(
            summary=summary,
            schema=schema,
        )