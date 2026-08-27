import json
from pathlib import Path

from app.services.rag.retriever import (
    KnowledgeRetriever,
)


def main() -> None:
    backend_dir = Path(
        __file__
    ).resolve().parents[3]

    test_file = (
        backend_dir
        / "database"
        / "evaluation"
        / "rag_test_cases.json"
    )

    test_cases = json.loads(
        test_file.read_text(
            encoding="utf-8"
        )
    )

    retriever = KnowledgeRetriever()

    for case_index, case in enumerate(
        test_cases,
        start=1,
    ):
        question = case["question"]
        category = case.get("category")

        print("\n")
        print("=" * 80)
        print(
            f"TEST CASE {case_index}"
        )
        print(
            "QUESTION:",
            question,
        )
        print(
            "CATEGORY:",
            category,
        )
        print("=" * 80)

        results = retriever.retrieve(
            query=question,
            top_k=5,
            category=category,
        )

        for rank, item in enumerate(
            results,
            start=1,
        ):
            print(
                f"\n--- RANK {rank} ---"
            )
            print(
                "chunk_id:",
                item.chunk_id,
            )
            print(
                "source:",
                item.source,
            )
            print(
                "page:",
                item.page,
            )
            print(
                "distance:",
                item.distance,
            )
            print(
                "content:",
                item.content[:600],
            )


if __name__ == "__main__":
    main()