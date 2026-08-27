import json
from pathlib import Path

from app.services.rag.retriever import (
    KnowledgeRetriever,
)


TOP_K = 5

GROUND_TRUTH_PATH = Path(
    "tests/ground_truth.json"
)


retriever = KnowledgeRetriever()


def load_ground_truth():
    with open(
        GROUND_TRUTH_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def retrieve(
    question: str,
    category: str | None = None,
    top_k: int = 5,
):
    results = retriever.retrieve(
        query=question,
        top_k=top_k,
        category=category,
    )

    retrieved_ids = []

    for item in results:
        if item.chunk_id:
            retrieved_ids.append(
                item.chunk_id
            )

    return retrieved_ids



def precision_at_k(
    retrieved_ids,
    relevant_ids,
    k=5,
):
    retrieved_k = retrieved_ids[:k]

    relevant = set(
        relevant_ids
    )

    if not retrieved_k:
        return 0.0

    hits = sum(
        1
        for chunk_id in retrieved_k
        if chunk_id in relevant
    )

    return hits / k


def recall_at_k(
    retrieved_ids,
    relevant_ids,
    k=5,
):
    relevant = set(
        relevant_ids
    )

    if not relevant:
        return 0.0

    retrieved_k = set(
        retrieved_ids[:k]
    )

    hits = len(
        retrieved_k.intersection(
            relevant
        )
    )

    return hits / len(
        relevant
    )


def hit_at_k(
    retrieved_ids,
    relevant_ids,
    k=5,
):
    relevant = set(
        relevant_ids
    )

    for chunk_id in retrieved_ids[:k]:
        if chunk_id in relevant:
            return 1.0

    return 0.0


def reciprocal_rank(
    retrieved_ids,
    relevant_ids,
):
    relevant = set(
        relevant_ids
    )

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant:
            return 1.0 / rank

    return 0.0


def get_first_relevant_rank(
    retrieved_ids,
    relevant_ids,
):
    relevant = set(
        relevant_ids
    )

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant:
            return rank

    return None


def main():
    cases = load_ground_truth()

    if not cases:
        print(
            "Không có ground truth."
        )
        return

    total_precision = 0.0
    total_recall = 0.0
    total_hit1 = 0.0
    total_hit3 = 0.0
    total_hit5 = 0.0
    total_rr = 0.0

    rows = []

    print(
        "\n"
        + "=" * 100
    )

    print(
        "RAG RETRIEVAL BENCHMARK"
    )

    print(
        "=" * 100
    )

    for index, case in enumerate(
        cases,
        start=1,
    ):
        question = case[
            "question"
        ]

        category = case.get(
            "category",
            "unknown",
        )

        relevant_ids = case.get(
            "reference_chunk_ids",
            [],
        )

        if not relevant_ids:
            print(
                f"Q{index:02d}: "
                "SKIPPED - "
                "reference_chunk_ids "
                "đang trống"
            )
            continue

        retrieved_ids = retrieve(
            question=question,
            category=category,
            top_k=TOP_K,
        )

        precision = precision_at_k(
            retrieved_ids,
            relevant_ids,
            TOP_K,
        )

        recall = recall_at_k(
            retrieved_ids,
            relevant_ids,
            TOP_K,
        )

        hit1 = hit_at_k(
            retrieved_ids,
            relevant_ids,
            1,
        )

        hit3 = hit_at_k(
            retrieved_ids,
            relevant_ids,
            3,
        )

        hit5 = hit_at_k(
            retrieved_ids,
            relevant_ids,
            5,
        )

        rr = reciprocal_rank(
            retrieved_ids,
            relevant_ids,
        )

        rank = get_first_relevant_rank(
            retrieved_ids,
            relevant_ids,
        )

        total_precision += precision
        total_recall += recall
        total_hit1 += hit1
        total_hit3 += hit3
        total_hit5 += hit5
        total_rr += rr

        rows.append(
            {
                "id": index,
                "question": question,
                "category": category,
                "rank": rank,
                "precision": precision,
                "recall": recall,
                "hit_at_1": hit1,
                "hit_at_3": hit3,
                "hit_at_5": hit5,
                "rr": rr,
                "retrieved_ids": (
                    retrieved_ids
                ),
            }
        )

        print()

        print(
            f"Q{index:02d} "
            f"[{category}]"
        )

        print(
            f"Question: {question}"
        )

        print(
            "Reference:"
        )

        for reference_id in relevant_ids:
            print(
                f"  - {reference_id}"
            )

        print(
            "Retrieved:"
        )

        for result_rank, chunk_id in enumerate(
            retrieved_ids,
            start=1,
        ):
            marker = (
                "✅"
                if chunk_id
                in set(relevant_ids)
                else "  "
            )

            print(
                f"  {marker} "
                f"Rank {result_rank}: "
                f"{chunk_id}"
            )

        print(
            f"First relevant rank: "
            f"{rank}"
        )

        print(
            f"P@5={precision:.4f} | "
            f"R@5={recall:.4f} | "
            f"Hit@1={hit1:.4f} | "
            f"Hit@3={hit3:.4f} | "
            f"Hit@5={hit5:.4f} | "
            f"RR={rr:.4f}"
        )

        print(
            "-" * 100
        )

    n = len(rows)

    if n == 0:
        print(
            "Không có case hợp lệ."
        )
        return

    avg_precision = (
        total_precision / n
    )

    avg_recall = (
        total_recall / n
    )

    avg_hit1 = (
        total_hit1 / n
    )

    avg_hit3 = (
        total_hit3 / n
    )

    avg_hit5 = (
        total_hit5 / n
    )

    mrr = (
        total_rr / n
    )

    print()

    print(
        "=" * 100
    )

    print(
        "FINAL RESULTS"
    )

    print(
        "=" * 100
    )

    print(
        f"Evaluated queries : {n}"
    )

    print(
        f"Precision@5       : "
        f"{avg_precision:.4f}"
    )

    print(
        f"Recall@5          : "
        f"{avg_recall:.4f}"
    )

    print(
        f"Hit@1             : "
        f"{avg_hit1:.4f}"
    )

    print(
        f"Hit@3             : "
        f"{avg_hit3:.4f}"
    )

    print(
        f"Hit@5             : "
        f"{avg_hit5:.4f}"
    )

    print(
        f"MRR               : "
        f"{mrr:.4f}"
    )

    output = {
        "top_k": TOP_K,
        "evaluated_queries": n,
        "metrics": {
            "precision_at_5": (
                avg_precision
            ),
            "recall_at_5": (
                avg_recall
            ),
            "hit_at_1": (
                avg_hit1
            ),
            "hit_at_3": (
                avg_hit3
            ),
            "hit_at_5": (
                avg_hit5
            ),
            "mrr": mrr,
        },
        "results": rows,
    }

    output_path = Path(
        "tests/"
        "rag_benchmark_results.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()

    print(
        "Đã lưu kết quả:"
    )

    print(
        output_path
    )


if __name__ == "__main__":
    main()