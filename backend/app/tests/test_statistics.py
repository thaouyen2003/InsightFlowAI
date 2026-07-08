import pandas as pd

from app.services.statistics import StatisticsCalculator


def main():
    df = pd.DataFrame(
        {
            "age": [20, 22, 25, 30, 35],
            "city": ["HCM", "HN", "HCM", "DN", "HCM"],
        }
    )

    print("=" * 60)
    print("NUMERIC")
    print("=" * 60)
    print(
        StatisticsCalculator.numeric(df["age"])
    )

    print()

    print("=" * 60)
    print("COMMON")
    print("=" * 60)
    print(
        StatisticsCalculator.common(df["age"])
    )

    print()

    print("=" * 60)
    print("CATEGORICAL")
    print("=" * 60)
    print(
        StatisticsCalculator.categorical(df["city"])
    )


if __name__ == "__main__":
    main()