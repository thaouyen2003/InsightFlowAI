"""
profiler.py

Dataset profiling service for InsightFlow AI.

Author: InsightFlow AI
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.semantic import SemanticDetector
from app.services.statistics import StatisticsCalculator


class DataProfiler:
    """
    Build a complete profile for a pandas DataFrame.
    """

    def profile(self, df: pd.DataFrame) -> dict[str, Any]:
        self._validate_dataframe(df)

        summary = self._build_summary(df)

        columns = [
            self._profile_column(column_name, df[column_name])
            for column_name in df.columns
        ]

        return {
            "summary": summary,
            "columns": columns,
        }

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> None:
        if df is None:
            raise ValueError("DataFrame cannot be None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if df.empty:
            raise ValueError("DataFrame is empty.")

    @staticmethod
    def _build_summary(df: pd.DataFrame) -> dict[str, Any]:
        return {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "numeric_columns": int(
                len(df.select_dtypes(include="number").columns)
            ),
            "categorical_columns": int(
                len(df.select_dtypes(include="object").columns)
            ),
            "datetime_columns": int(
                len(df.select_dtypes(include="datetime").columns)
            ),
            "boolean_columns": int(
                len(df.select_dtypes(include="bool").columns)
            ),
            "duplicates": int(df.duplicated().sum()),
            "missing_cells": int(df.isna().sum().sum()),
        }

    def _profile_column(
        self,
        column_name: str,
        series: pd.Series,
    ) -> dict[str, Any]:

        profile = {
            "name": column_name,
            "dtype": str(series.dtype),
            "semantic_type": SemanticDetector.detect(
                column_name,
                series,
            ),
        }

        profile.update(
            StatisticsCalculator.common(series)
        )

        if pd.api.types.is_numeric_dtype(series):

            profile["statistics"] = (
                StatisticsCalculator.numeric(series)
            )

        else:

            profile["statistics"] = (
                StatisticsCalculator.categorical(series)
            )

        return profile