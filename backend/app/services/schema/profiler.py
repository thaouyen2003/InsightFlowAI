"""
Column Profiler

Nhiệm vụ:
- Phân tích một cột trong DataFrame.
- Thu thập metadata để Schema Analyzer sử dụng.
"""

import pandas as pd

from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
)

from app.services.schema.detector import SemanticDetector
from app.services.schema.models import ColumnProfile


class ColumnProfiler:

    def profile(
        self,
        df: pd.DataFrame,
        column: str,
    ) -> ColumnProfile:
        """
        Phân tích một cột trong DataFrame.
        """

        series = df[column]

        statistics = {}

        # ====================================
        # Nếu là cột số thì tính thống kê
        # ====================================

        if is_numeric_dtype(series):

            statistics = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "median": float(series.median()),
            }

        # ====================================
        # Tạo object ColumnProfile
        # ====================================

        profile = ColumnProfile(

            name=column,

            dtype=str(series.dtype),

            semantic_type=SemanticDetector.detect(column),

            missing=int(series.isna().sum()),

            unique=int(series.nunique()),

            sample=series.dropna().head(5).tolist(),

            statistics=statistics,
        )

        # ====================================
        # Primary Key Detection
        # Điều kiện:
        # - Không có NULL
        # - Unique = số dòng
        # ====================================

        if (
            profile.unique == len(df)
            and profile.missing == 0
        ):
            profile.is_primary_key = True

        return profile