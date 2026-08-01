import pandas as pd

from app.services.dashboard.data_cleaner import (
    DataCleaner,
)
from app.services.semantic_analysis.column_analyzer import (
    ColumnAnalyzer,
)


def test_data_cleaner():
    df = pd.DataFrame({
        "order_id": [
            "001",
            "002",
            "003",
        ],
        "order_date": [
            "21/07/2026",
            "22/07/2026",
            "23/07/2026",
        ],
        "revenue": [
            "1,200,000",
            "850,000",
            "$450",
        ],
        "discount": [
            "10%",
            "20%",
            "15.5%",
        ],
        "active": [
            "YES",
            "NO",
            "YES",
        ],
        "category": [
            "  Laptop ",
            "Phone",
            "Laptop   Accessories",
        ],
        "notes": [
            "N/A",
            "Good",
            "-",
        ],
    })

    analyzer = ColumnAnalyzer()

    metadata = analyzer.analyze(df)

    cleaner = DataCleaner()

    cleaned_df, warnings = cleaner.clean(
        df=df,
        columns_metadata=metadata,
    )

    assert cleaned_df["order_id"].tolist() == [
        "001",
        "002",
        "003",
    ]

    assert pd.api.types.is_datetime64_any_dtype(
        cleaned_df["order_date"]
    )

    assert pd.api.types.is_numeric_dtype(
        cleaned_df["revenue"]
    )

    assert cleaned_df["revenue"].tolist() == [
        1200000,
        850000,
        450,
    ]

    assert pd.api.types.is_numeric_dtype(
        cleaned_df["discount"]
    )

    assert cleaned_df["discount"].tolist() == [
        10.0,
        20.0,
        15.5,
    ]

    assert pd.api.types.is_bool_dtype(
        cleaned_df["active"]
    )

    assert cleaned_df["active"].tolist() == [
        True,
        False,
        True,
    ]

    assert cleaned_df["category"].tolist() == [
        "Laptop",
        "Phone",
        "Laptop Accessories",
    ]

    assert pd.isna(
        cleaned_df["notes"].iloc[0]
    )

    assert pd.isna(
        cleaned_df["notes"].iloc[2]
    )

    assert len(warnings) > 0