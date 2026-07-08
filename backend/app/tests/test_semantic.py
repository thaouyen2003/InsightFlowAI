import pandas as pd

from app.services.semantic import SemanticDetector


def test():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "customer_city": ["HCM", "HN", "DN"],
        "customer_state": ["SG", "HN", "DN"],
        "price": [10.5, 20.3, 15.6],
        "review_score": [5, 4, 3],
        "is_active": [True, False, True],
        "description": [
            "Good product",
            "Excellent",
            "Average"
        ]
    })

    for column in df.columns:
        semantic = SemanticDetector.detect(
            column,
            df[column]
        )

        print(f"{column:20} -> {semantic}")


if __name__ == "__main__":
    test()