"""
statistics.py

Utility class for calculating descriptive statistics
used by the Data Profiler.

Author: InsightFlow AI
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class StatisticsCalculator:
    """
    Calculate statistics for numeric and categorical columns.
    """

    @staticmethod
    def numeric(series: pd.Series) -> dict[str, Any]:
        """
        Calculate statistics for numeric data.

        Parameters
        ----------
        series : pd.Series

        Returns
        -------
        dict
        """

        clean = series.dropna()

        if clean.empty:
            return {
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std": None,
                "variance": None,
                "sum": None,
            }

        return {
            "min": float(clean.min()),
            "max": float(clean.max()),
            "mean": round(float(clean.mean()), 2),
            "median": round(float(clean.median()), 2),
            "std": round(float(clean.std()), 2),
            "variance": round(float(clean.var()), 2),
            "sum": round(float(clean.sum()), 2),
        }

    @staticmethod
    def categorical(series: pd.Series, top_n: int = 5) -> dict[str, Any]:
        """
        Calculate statistics for categorical data.
        """

        clean = series.dropna()

        top_values = (
            clean.value_counts()
            .head(top_n)
            .items()
        )

        return {
            "top_values": [
                {
                    "value": str(value),
                    "count": int(count),
                }
                for value, count in top_values
            ]
        }

    @staticmethod
    def common(series: pd.Series) -> dict[str, Any]:
        """
        Statistics shared by every datatype.
        """

        total = len(series)

        missing = int(series.isna().sum())

        unique = int(series.nunique(dropna=True))
        
        duplicate = int(series.duplicated().sum())

        # duplicate = max(total - unique, 0)

        return {
            "missing": missing,
            "missing_percent": round(missing / total * 100, 2)
            if total
            else 0,
            "unique": unique,
            "unique_percent": round(unique / total * 100, 2)
            if total
            else 0,
            "duplicates": duplicate,
            "sample": [
                str(v)
                for v in series.dropna().head(5).tolist()
            ],
        }