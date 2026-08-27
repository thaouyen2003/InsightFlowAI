import json
from pathlib import Path
from typing import Any

from app.services.rag.retriever import (
    KnowledgeRetriever,
)


class IDRetrievalEvaluation:
    """
    Đánh giá chất lượng Retrieval bằng chunk_id.

    Metrics:
    - Precision@K
    - Recall@K
    - Hit@1
    - Hit@3
    - Hit@5
    - MRR

    Hỗ trợ ba cấu hình:

    1. baseline
       Semantic vector retrieval thuần túy.

    2. semantic_lexical
       Semantic retrieval Top-20
       + semantic rank score
       + lexical overlap
       + reranking.

    3. optimized
       Semantic retrieval Top-20
       + semantic rank score
       + lexical overlap
       + phrase boost
       + reranking.
    """

    def __init__(self) -> None:
        self.retriever = KnowledgeRetriever()

        evaluation_dir = Path(
            __file__
        ).resolve().parent

        self.test_file = (
            evaluation_dir
            / "ground_truth_candidates.json"
        )

    # =========================================================
    # LOAD TEST CASES
    # =========================================================

    def load_test_cases(
        self,
    ) -> list[dict[str, Any]]:
        """
        Đọc bộ test case.

        Hỗ trợ hai format:

        [
            {...},
            {...}
        ]

        hoặc:

        {
            "test_cases": [
                {...},
                {...}
            ]
        }
        """

        if not self.test_file.exists():
            raise FileNotFoundError(
                "Không tìm thấy RAG test dataset: "
                f"{self.test_file}"
            )

        data = json.loads(
            self.test_file.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            test_cases = data

        elif isinstance(data, dict):
            test_cases = data.get(
                "test_cases",
                []
            )

        else:
            raise ValueError(
                "RAG test dataset "
                "không đúng định dạng."
            )

        if not isinstance(
            test_cases,
            list,
        ):
            raise ValueError(
                "test_cases phải là danh sách."
            )

        return test_cases

    # =========================================================
    # RETRIEVAL
    # =========================================================

    def retrieve(
        self,
        question: str,
        category: str | None,
        top_k: int,
        mode: str = "optimized",
    ):
        """
        Thực hiện retrieval theo ba cấu hình.

        baseline:
            Semantic vector retrieval thuần túy.

        semantic_lexical:
            Semantic Top-20
            + lexical reranking
            không phrase boost.

        optimized:
            Semantic Top-20
            + lexical reranking
            + phrase boost.
        """

        # =====================================================
        # PRIMARY RETRIEVAL
        # =====================================================

        if mode == "baseline":
            retrieved_items = (
                self.retriever.retrieve(
                    query=question,
                    top_k=top_k,
                    category=category,
                )
            )

        elif mode == "semantic_lexical":
            retrieved_items = (
                self.retriever.retrieve_semantic_lexical(
                    query=question,
                    top_k=top_k,
                    candidate_k=20,
                    category=category,
                )
            )

        elif mode == "optimized":
            retrieved_items = (
                self.retriever.retrieve_optimized(
                    query=question,
                    top_k=top_k,
                    candidate_k=20,
                    category=category,
                )
            )

        else:
            raise ValueError(
                f"Retrieval mode không hợp lệ: "
                f"{mode}"
            )

        # =====================================================
        # FALLBACK
        #
        # Nếu filter category không có kết quả,
        # tìm lại trên toàn bộ Knowledge Base.
        # =====================================================

        if (
            not retrieved_items
            and category is not None
        ):
            if mode == "baseline":
                retrieved_items = (
                    self.retriever.retrieve(
                        query=question,
                        top_k=top_k,
                        category=None,
                    )
                )

            elif mode == "semantic_lexical":
                retrieved_items = (
                    self.retriever.retrieve_semantic_lexical(
                        query=question,
                        top_k=top_k,
                        candidate_k=20,
                        category=None,
                    )
                )

            elif mode == "optimized":
                retrieved_items = (
                    self.retriever.retrieve_optimized(
                        query=question,
                        top_k=top_k,
                        candidate_k=20,
                        category=None,
                    )
                )

        return retrieved_items

    # =========================================================
    # EVALUATE ONE CASE
    # =========================================================

    def evaluate_case(
        self,
        test_case: dict[str, Any],
        top_k: int = 5,
        mode: str = "optimized",
    ) -> dict[str, Any]:
        """
        Đánh giá một test case.
        """

        question = str(
            test_case.get(
                "question",
                "",
            )
        ).strip()

        if not question:
            raise ValueError(
                "Test case thiếu question."
            )

        category = test_case.get(
            "category"
        )

        raw_reference_ids = (
            test_case.get(
                "reference_chunk_ids",
                [],
            )
        )

        if not isinstance(
            raw_reference_ids,
            list,
        ):
            raise ValueError(
                "reference_chunk_ids "
                "phải là danh sách."
            )

        reference_chunk_ids = {
            str(chunk_id).strip()
            for chunk_id in raw_reference_ids
            if str(chunk_id).strip()
        }

        if not reference_chunk_ids:
            raise ValueError(
                "Test case chưa có "
                "reference_chunk_ids."
            )

        # =====================================================
        # RETRIEVE
        # =====================================================

        retrieved_items = self.retrieve(
            question=question,
            category=category,
            top_k=top_k,
            mode=mode,
        )

        retrieved_chunk_ids = [
            item.chunk_id
            for item in retrieved_items
        ]

        retrieved_set = set(
            retrieved_chunk_ids
        )

        relevant_retrieved = (
            retrieved_set
            & reference_chunk_ids
        )

        relevant_count = len(
            relevant_retrieved
        )

        # =====================================================
        # PRECISION@K
        # =====================================================

        precision = (
            relevant_count
            / len(retrieved_chunk_ids)
            if retrieved_chunk_ids
            else 0.0
        )

        # =====================================================
        # RECALL@K
        # =====================================================

        recall = (
            relevant_count
            / len(reference_chunk_ids)
            if reference_chunk_ids
            else 0.0
        )

        # =====================================================
        # HIT@K
        # =====================================================

        hit_at_k = (
            1.0
            if relevant_count > 0
            else 0.0
        )

        hit_at_1 = (
            1.0
            if any(
                chunk_id
                in reference_chunk_ids
                for chunk_id
                in retrieved_chunk_ids[:1]
            )
            else 0.0
        )

        hit_at_3 = (
            1.0
            if any(
                chunk_id
                in reference_chunk_ids
                for chunk_id
                in retrieved_chunk_ids[:3]
            )
            else 0.0
        )

        hit_at_5 = (
            1.0
            if any(
                chunk_id
                in reference_chunk_ids
                for chunk_id
                in retrieved_chunk_ids[:5]
            )
            else 0.0
        )

        # =====================================================
        # MRR
        # =====================================================

        first_relevant_rank: int | None = None

        for rank, chunk_id in enumerate(
            retrieved_chunk_ids,
            start=1,
        ):
            if (
                chunk_id
                in reference_chunk_ids
            ):
                first_relevant_rank = rank
                break

        reciprocal_rank = (
            1.0 / first_relevant_rank
            if first_relevant_rank
            else 0.0
        )

        # =====================================================
        # RETRIEVED DETAILS
        # =====================================================

        retrieved_details = [
            {
                "rank": index,
                "chunk_id": item.chunk_id,
                "source": item.source,
                "page": item.page,
                "category": item.category,
                "distance": item.distance,
                "is_relevant": (
                    item.chunk_id
                    in reference_chunk_ids
                ),
                "content_preview":
                    item.content[:250],
            }
            for index, item in enumerate(
                retrieved_items,
                start=1,
            )
        ]

        return {
            "question":
                question,
            "category":
                category,
            "retrieval_mode":
                mode,
            "top_k":
                top_k,
            "reference_chunk_ids":
                list(
                    reference_chunk_ids
                ),
            "retrieved_chunk_ids":
                retrieved_chunk_ids,
            "relevant_retrieved":
                list(
                    relevant_retrieved
                ),
            "precision":
                precision,
            "recall":
                recall,
            "hit_at_k":
                hit_at_k,
            "hit_at_1":
                hit_at_1,
            "hit_at_3":
                hit_at_3,
            "hit_at_5":
                hit_at_5,
            "mrr":
                reciprocal_rank,
            "first_relevant_rank":
                first_relevant_rank,
            "retrieved_details":
                retrieved_details,
        }

    # =========================================================
    # EVALUATE FULL DATASET
    # =========================================================

    def evaluate(
        self,
        limit: int | None = None,
        top_k: int = 5,
        mode: str = "optimized",
    ) -> dict[str, Any]:
        """
        Đánh giá toàn bộ benchmark dataset.
        """

        if top_k <= 0:
            raise ValueError(
                "top_k phải lớn hơn 0."
            )

        valid_modes = {
            "baseline",
            "semantic_lexical",
            "optimized",
        }

        if mode not in valid_modes:
            raise ValueError(
                "mode phải là "
                "'baseline', "
                "'semantic_lexical' "
                "hoặc 'optimized'."
            )

        test_cases = (
            self.load_test_cases()
        )

        if limit is not None:
            if limit <= 0:
                raise ValueError(
                    "limit phải lớn hơn 0."
                )

            test_cases = (
                test_cases[:limit]
            )

        results: list[
            dict[str, Any]
        ] = []

        skipped_cases: list[
            dict[str, Any]
        ] = []

        # =====================================================
        # RUN BENCHMARK
        # =====================================================

        for index, test_case in enumerate(
            test_cases,
            start=1,
        ):
            question = str(
                test_case.get(
                    "question",
                    "",
                )
            ).strip()

            print(
                f"[ID RETRIEVAL EVAL] "
                f"{index}/{len(test_cases)} "
                f"[{mode}]: "
                f"{question}"
            )

            try:
                case_result = (
                    self.evaluate_case(
                        test_case=test_case,
                        top_k=top_k,
                        mode=mode,
                    )
                )

                results.append(
                    case_result
                )

            except ValueError as error:
                skipped_cases.append(
                    {
                        "question":
                            question,
                        "reason":
                            str(error),
                    }
                )

                print(
                    "[SKIPPED]",
                    question,
                    "-",
                    error,
                )

        # =====================================================
        # EMPTY RESULT
        # =====================================================

        if not results:
            return {
                "retrieval_mode":
                    mode,
                "total_cases":
                    len(test_cases),
                "evaluated_cases":
                    0,
                "skipped_cases":
                    len(skipped_cases),
                "precision":
                    0.0,
                "recall":
                    0.0,
                "hit_at_k":
                    0.0,
                "hit_at_1":
                    0.0,
                "hit_at_3":
                    0.0,
                "hit_at_5":
                    0.0,
                "mrr":
                    0.0,
                "category_summary":
                    {},
                "results":
                    [],
                "skipped":
                    skipped_cases,
            }

        evaluated_count = len(
            results
        )

        # =====================================================
        # GLOBAL METRICS
        # =====================================================

        mean_precision = (
            sum(
                item["precision"]
                for item in results
            )
            / evaluated_count
        )

        mean_recall = (
            sum(
                item["recall"]
                for item in results
            )
            / evaluated_count
        )

        mean_hit_at_k = (
            sum(
                item["hit_at_k"]
                for item in results
            )
            / evaluated_count
        )

        mean_hit_at_1 = (
            sum(
                item["hit_at_1"]
                for item in results
            )
            / evaluated_count
        )

        mean_hit_at_3 = (
            sum(
                item["hit_at_3"]
                for item in results
            )
            / evaluated_count
        )

        mean_hit_at_5 = (
            sum(
                item["hit_at_5"]
                for item in results
            )
            / evaluated_count
        )

        mean_mrr = (
            sum(
                item["mrr"]
                for item in results
            )
            / evaluated_count
        )

        # =====================================================
        # CATEGORY BREAKDOWN
        # =====================================================

        category_stats: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for item in results:
            category = (
                item["category"]
                or "unknown"
            )

            if (
                category
                not in category_stats
            ):
                category_stats[
                    category
                ] = []

            category_stats[
                category
            ].append(
                item
            )

        category_summary: dict[
            str,
            dict[str, Any],
        ] = {}

        for (
            category,
            items,
        ) in category_stats.items():

            count = len(
                items
            )

            category_summary[
                category
            ] = {
                "count":
                    count,
                "precision":
                    sum(
                        item["precision"]
                        for item in items
                    )
                    / count,
                "recall":
                    sum(
                        item["recall"]
                        for item in items
                    )
                    / count,
                "hit_at_1":
                    sum(
                        item["hit_at_1"]
                        for item in items
                    )
                    / count,
                "hit_at_3":
                    sum(
                        item["hit_at_3"]
                        for item in items
                    )
                    / count,
                "hit_at_5":
                    sum(
                        item["hit_at_5"]
                        for item in items
                    )
                    / count,
                "mrr":
                    sum(
                        item["mrr"]
                        for item in items
                    )
                    / count,
            }

        # =====================================================
        # FINAL RESULT
        # =====================================================

        return {
            "retrieval_mode":
                mode,
            "total_cases":
                len(test_cases),
            "evaluated_cases":
                evaluated_count,
            "skipped_cases":
                len(skipped_cases),
            "precision":
                mean_precision,
            "recall":
                mean_recall,
            "hit_at_k":
                mean_hit_at_k,
            "hit_at_1":
                mean_hit_at_1,
            "hit_at_3":
                mean_hit_at_3,
            "hit_at_5":
                mean_hit_at_5,
            "mrr":
                mean_mrr,
            "category_summary":
                category_summary,
            "results":
                results,
            "skipped":
                skipped_cases,
        }


# =============================================================
# PRINT SUMMARY
# =============================================================


def print_evaluation_summary(
    result: dict[str, Any],
) -> None:
    """
    In kết quả benchmark dễ đọc.
    """

    print(
        "\n=== ID RETRIEVAL EVALUATION ==="
    )

    print(
        "Retrieval mode:",
        result.get(
            "retrieval_mode",
            "unknown",
        ),
    )

    print(
        "Total cases:",
        result["total_cases"],
    )

    print(
        "Evaluated:",
        result["evaluated_cases"],
    )

    print(
        "Skipped:",
        result["skipped_cases"],
    )

    print(
        "Precision@5:",
        f'{result["precision"] * 100:.2f}%',
    )

    print(
        "Recall@5:",
        f'{result["recall"] * 100:.2f}%',
    )

    print(
        "Hit@1:",
        f'{result["hit_at_1"] * 100:.2f}%',
    )

    print(
        "Hit@3:",
        f'{result["hit_at_3"] * 100:.2f}%',
    )

    print(
        "Hit@5:",
        f'{result["hit_at_5"] * 100:.2f}%',
    )

    print(
        "MRR:",
        f'{result["mrr"]:.4f}',
    )

    # =========================================================
    # CATEGORY BREAKDOWN
    # =========================================================

    print(
        "\n=== CATEGORY BREAKDOWN ==="
    )

    for category, stats in (
        result[
            "category_summary"
        ].items()
    ):
        print(
            f"\n[{category}]"
        )

        print(
            "Cases:",
            stats["count"],
        )

        print(
            "Precision@5:",
            f'{stats["precision"] * 100:.2f}%',
        )

        print(
            "Recall@5:",
            f'{stats["recall"] * 100:.2f}%',
        )

        print(
            "Hit@1:",
            f'{stats["hit_at_1"] * 100:.2f}%',
        )

        print(
            "Hit@3:",
            f'{stats["hit_at_3"] * 100:.2f}%',
        )

        print(
            "Hit@5:",
            f'{stats["hit_at_5"] * 100:.2f}%',
        )

        print(
            "MRR:",
            f'{stats["mrr"]:.4f}',
        )

    # =========================================================
    # FAILED CASES
    # =========================================================

    print(
        "\n=== FAILED CASES ==="
    )

    failed = [
        item
        for item in result["results"]
        if item["hit_at_5"] == 0
    ]

    if not failed:
        print(
            "No failed cases."
        )

    else:
        for item in failed:
            print(
                "\nQuestion:",
                item["question"],
            )

            print(
                "Category:",
                item["category"],
            )

            print(
                "References:",
                item[
                    "reference_chunk_ids"
                ],
            )

            print(
                "Retrieved:",
                item[
                    "retrieved_chunk_ids"
                ],
            )

            print(
                "First relevant rank:",
                item[
                    "first_relevant_rank"
                ],
            )

    # =========================================================
    # LOW-RANK CASES
    # =========================================================

    print(
        "\n=== LOW-RANK RETRIEVAL CASES ==="
    )

    low_rank_cases = [
        item
        for item in result["results"]
        if (
            item[
                "first_relevant_rank"
            ] is not None
            and item[
                "first_relevant_rank"
            ] > 1
        )
    ]

    low_rank_cases.sort(
        key=lambda item: (
            -item[
                "first_relevant_rank"
            ],
            item[
                "category"
            ] or "",
        )
    )

    if not low_rank_cases:
        print(
            "No low-rank cases."
        )

    else:
        for item in low_rank_cases:
            print(
                "\nQuestion:",
                item["question"],
            )

            print(
                "Category:",
                item["category"],
            )

            print(
                "References:",
                item[
                    "reference_chunk_ids"
                ],
            )

            print(
                "First relevant rank:",
                item[
                    "first_relevant_rank"
                ],
            )

            print(
                "Recall:",
                f'{item["recall"] * 100:.2f}%',
            )

            print(
                "Retrieved details:"
            )

            for detail in item[
                "retrieved_details"
            ]:
                marker = (
                    " <-- RELEVANT"
                    if detail[
                        "is_relevant"
                    ]
                    else ""
                )

                print(
                    f'  Rank '
                    f'{detail["rank"]}: '
                    f'{detail["chunk_id"]}'
                    f'{marker}'
                )

                print(
                    "    Distance:",
                    detail["distance"],
                )

                print(
                    "    Preview:",
                    detail[
                        "content_preview"
                    ],
                )


# =============================================================
# RUN EXPERIMENTS
# =============================================================


if __name__ == "__main__":
    service = (
        IDRetrievalEvaluation()
    )

    # =========================================================
    # EXPERIMENT 1
    # SEMANTIC-ONLY BASELINE
    # =========================================================

    print(
        "\n"
        "========================================"
    )

    print(
        "EXPERIMENT 1: "
        "SEMANTIC-ONLY BASELINE"
    )

    print(
        "========================================"
    )

    baseline_result = (
        service.evaluate(
            top_k=5,
            mode="baseline",
        )
    )

    print_evaluation_summary(
        baseline_result
    )

    # =========================================================
    # EXPERIMENT 2
    # SEMANTIC + LEXICAL
    # =========================================================

    print(
        "\n"
        "========================================"
    )

    print(
        "EXPERIMENT 2: "
        "SEMANTIC + LEXICAL"
    )

    print(
        "========================================"
    )

    semantic_lexical_result = (
        service.evaluate(
            top_k=5,
            mode="semantic_lexical",
        )
    )

    print_evaluation_summary(
        semantic_lexical_result
    )

    # =========================================================
    # EXPERIMENT 3
    # SEMANTIC + LEXICAL + PHRASE BOOST
    # =========================================================

    print(
        "\n"
        "========================================"
    )

    print(
        "EXPERIMENT 3: "
        "SEMANTIC + LEXICAL + PHRASE BOOST"
    )

    print(
        "========================================"
    )
    optimized_result = (
        service.evaluate(
            top_k=5,
            mode="optimized",
        )
    )

    print_evaluation_summary(
        optimized_result
    )