"""
test_profiler.py

Unit test for DataProfiler.
"""

import json

import pandas as pd

from app.services.profiler import DataProfiler


def main() -> None:
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "customer_city": [
                "HCM",
                "HN",
                "HCM",
                "DN",
            ],
            "price": [
                100.5,
                200.0,
                150.5,
                300.0,
            ],
            "is_active": [
                True,
                True,
                False,
                True,
            ],
        }
    )

    profiler = DataProfiler()

    result = profiler.profile(df)

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()