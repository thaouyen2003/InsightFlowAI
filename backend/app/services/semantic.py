"""
semantic.py

Semantic type detection for InsightFlow AI.

This module infers the business meaning of a column
based on:

1. Column name
2. Pandas dtype
3. Sample values (future extension)

Author: InsightFlow AI
"""

from __future__ import annotations

import re
from typing import Final

import pandas as pd


class SemanticDetector:
    """
    Detect semantic meaning of a dataframe column.

    Examples
    --------
    customer_id            -> identifier
    customer_city          -> city
    price                  -> currency
    order_purchase_date    -> datetime
    review_score           -> score
    """

    # ------------------------------------------------------------------
    # Keyword dictionary
    # ------------------------------------------------------------------

    KEYWORD_MAP: Final[dict[str, tuple[str, ...]]] = {

        "identifier": (
            "id",
            "uuid",
            "key",
            "code",
            "identifier",
        ),

        "currency": (
            "price",
            "amount",
            "cost",
            "revenue",
            "profit",
            "income",
            "expense",
            "payment",
            "freight",
            "salary",
            "fee",
            "total",
        ),

        "datetime": (
            "date",
            "time",
            "timestamp",
            "created",
            "updated",
            "purchase",
            "delivery",
        ),

        "email": (
            "email",
            "mail",
        ),

        "phone": (
            "phone",
            "mobile",
            "telephone",
            "contact",
        ),

        "zipcode": (
            "zip",
            "zipcode",
            "postal",
            "postcode",
        ),

        "city": (
            "city",
        ),

        "state": (
            "state",
            "province",
        ),

        "country": (
            "country",
            "nation",
        ),

        "percentage": (
            "percent",
            "percentage",
            "rate",
            "ratio",
        ),

        "score": (
            "score",
            "rating",
            "rank",
            "grade",
        ),

        "boolean": (
            "is_",
            "has_",
            "active",
            "enabled",
            "deleted",
            "available",
            "valid",
        ),
    }

    # ------------------------------------------------------------------

    @staticmethod
    def normalize(column_name: str) -> str:
        """
        Normalize column name.

        Example
        -------
        Customer-ID
        ↓
        customer id
        """

        column = column_name.lower()

        column = re.sub(r"[_\-]+", " ", column)

        column = re.sub(r"\s+", " ", column)

        return column.strip()

    # ------------------------------------------------------------------

    @classmethod
    def detect(
        cls,
        column_name: str,
        series: pd.Series,
    ) -> str:
        """
        Detect semantic type.
        """

        normalized = cls.normalize(column_name)

        # --------------------------------------------------------------
        # Rule 1
        # Keyword matching
        # --------------------------------------------------------------

        for semantic, keywords in cls.KEYWORD_MAP.items():

            for keyword in keywords:

                if keyword in normalized:
                    return semantic

        # --------------------------------------------------------------
        # Rule 2
        # Pandas dtype
        # --------------------------------------------------------------

        if pd.api.types.is_bool_dtype(series):
            return "boolean"

        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        # --------------------------------------------------------------
        # Rule 3
        # Cardinality
        # --------------------------------------------------------------

        unique_ratio = (
            series.nunique(dropna=True) / len(series)
            if len(series)
            else 0
        )

        if unique_ratio < 0.3:
            return "category"

        return "text"