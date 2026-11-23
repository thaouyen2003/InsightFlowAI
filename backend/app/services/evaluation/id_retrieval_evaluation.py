import json
from pathlib import Path
from typing import Any

from app.services.rag.bm25_retriever import (
    BM25Retriever,
)
from app.services.rag.retriever import (
    KnowledgeRetriever,
)
from app.services.rag.hybrid_retriever import (
    HybridRetriever,
)

class IDRetrievalEvaluation:
    """
    Đánh giá chất lượng retrieval bằng exact chunk-ID matching.

    Metrics:
    - Precision@K
    - Recall@K
    - Hit@1
    - Hit@3
    - Hit@5
    - Mean Reciprocal Rank (MRR)

    Retrieval configurations:

    1. baseline
       Semantic vector retrieval thuần túy.

    2. bm25
       BM25 lexical retrieval baseline.

    3. semantic_lexical
       Semantic retrieval Top-20
       + semantic rank score
       + lexical overlap
       + reranking.

    4. optimized
       Semantic retrieval Top-20
       + semantic rank score
       + lexical overlap
       + phrase boost
       + reranking.

    Output:
    - Aggregate metrics.
    - Domain-level metrics.
    - Per-query metrics.
    - Retrieved chunk details.
    - JSON result file cho từng retrieval mode.
    """

    VALID_MODES = {
        "baseline",
        "bm25",
        "hybrid_rrf",
        "semantic_lexical",
        "optimized",
        "weight_60_40",
        "weight_50_50",
        "weight_40_60",
    }

    def __init__(self) -> None:
        # =====================================================
        # RETRIEVERS
        # =====================================================

        self.retriever = KnowledgeRetriever()

        self.bm25_retriever = BM25Retriever(
            vector_store=self.retriever.vector_store
        )

        self.hybrid_retriever = (
            HybridRetriever(
                dense_retriever=
                    self.retriever,

                bm25_retriever=
                    self.bm25_retriever,

                rrf_k=60,
            )
        )
        # =====================================================
        # PATHS
        # =====================================================

        self.evaluation_dir = (
            Path(__file__)
            .resolve()
            .parent
        )

        # =====================================================
        # BENCHMARK FILE
        #
        # Tạm thời giữ benchmark hiện tại để đảm bảo
        # kết quả mới có thể so sánh trực tiếp với
        # các experiment trước.
        # =====================================================

        self.test_file = (
            self.evaluation_dir
            / "ground_truth_evidence_final.json"
        )

        # =====================================================
        # OUTPUT DIRECTORY
        # =====================================================

        self.results_dir = (
            self.evaluation_dir
            / "results"
        )

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # LOAD TEST CASES
    # =========================================================

    def load_test_cases(
        self,
    ) -> list[dict[str, Any]]:
        """
        Đọc benchmark dataset.

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
                encoding="utf-8",
            )
        )

        if isinstance(data, list):
            test_cases = data

        elif isinstance(data, dict):
            test_cases = data.get(
                "test_cases",
                [],
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
        Thực hiện retrieval theo retrieval mode.

        Nếu category filter không trả về kết quả,
        hệ thống fallback và retrieval lại trên
        toàn bộ knowledge base.
        """

        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Retrieval mode không hợp lệ: "
                f"{mode}"
            )

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

        elif mode == "bm25":
            retrieved_items = (
                self.bm25_retriever.retrieve(
                    query=question,
                    top_k=top_k,
                    category=category,
                )
            )
        elif mode == "hybrid_rrf":
            retrieved_items = (
                self.hybrid_retriever.retrieve(
                    query=question,
                    top_k=top_k,
                    candidate_k=20,
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

        elif mode in {
            "weight_60_40",
            "weight_50_50",
            "weight_40_60",
        }:
            weight_configs = {
                "weight_60_40": (0.60, 0.40),
                "weight_50_50": (0.50, 0.50),
                "weight_40_60": (0.40, 0.60),
            }

            semantic_weight, lexical_weight = (
                weight_configs[mode]
            )

            retrieved_items = (
                self.retriever.retrieve_semantic_lexical(
                    query=question,
                    top_k=top_k,
                    candidate_k=20,
                    category=category,
                    semantic_weight=semantic_weight,
                    lexical_weight=lexical_weight,
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
        # Nếu category filter không có kết quả,
        # retrieval lại trên toàn bộ knowledge base.
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

            elif mode == "bm25":
                retrieved_items = (
                    self.bm25_retriever.retrieve(
                        query=question,
                        top_k=top_k,
                        category=None,
                    )
                )

            elif mode == "hybrid_rrf":
                retrieved_items = (
                    self.hybrid_retriever.retrieve(
                        query=question,
                        top_k=top_k,
                        candidate_k=20,
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
            elif mode in {
                "weight_60_40",
                "weight_50_50",
                "weight_40_60",
            }:
                weight_configs = {
                    "weight_60_40": (0.60, 0.40),
                    "weight_50_50": (0.50, 0.50),
                    "weight_40_60": (0.40, 0.60),
                }

                semantic_weight, lexical_weight = (
                    weight_configs[mode]
                )

                retrieved_items = (
                    self.retriever.retrieve_semantic_lexical(
                        query=question,
                        top_k=top_k,
                        candidate_k=20,
                        category=None,
                        semantic_weight=semantic_weight,
                        lexical_weight=lexical_weight,
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
        question_index: int | None = None,
    ) -> dict[str, Any]:
        """
        Đánh giá một câu hỏi benchmark.
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

        # =====================================================
        # QUESTION ID
        # =====================================================

        question_id = (
            test_case.get("id")
            or test_case.get("question_id")
            or question_index
        )

        # =====================================================
        # GROUND TRUTH
        #
        # reference_chunk_ids:
        #   Ground-truth gốc để truy vết.
        #
        # relevance_groups:
        #   Mỗi group là một evidence requirement.
        #   Các chunk trong cùng group được xem là
        #   các passage thay thế tương đương.
        # =====================================================

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

        original_reference_chunk_ids = {
            str(chunk_id).strip()
            for chunk_id in raw_reference_ids
            if str(chunk_id).strip()
        }

        if not original_reference_chunk_ids:
            raise ValueError(
                "Test case chưa có "
                "reference_chunk_ids."
            )

        raw_groups = test_case.get(
            "relevance_groups"
        )

        # Fallback cho benchmark cũ:
        # mỗi reference là một evidence group riêng.
        if raw_groups is None:
            raw_groups = [
                [chunk_id]
                for chunk_id
                in original_reference_chunk_ids
            ]

        if not isinstance(
            raw_groups,
            list,
        ):
            raise ValueError(
                "relevance_groups "
                "phải là danh sách."
            )

        relevance_groups: list[set[str]] = []

        for raw_group in raw_groups:
            if not isinstance(
                raw_group,
                list,
            ):
                raise ValueError(
                    "Mỗi relevance group "
                    "phải là một danh sách."
                )

            group = {
                str(chunk_id).strip()
                for chunk_id in raw_group
                if str(chunk_id).strip()
            }

            if group:
                relevance_groups.append(
                    group
                )

        if not relevance_groups:
            raise ValueError(
                "Test case chưa có "
                "relevance evidence."
            )

        relevant_chunk_ids = set().union(
            *relevance_groups
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
            & relevant_chunk_ids
        )

        hit_groups = sum(
            1
            for group in relevance_groups
            if retrieved_set & group
        )

        relevant_count = hit_groups

        # =====================================================
        # PRECISION@K
        # =====================================================

        precision_at_k = (
            relevant_count
            / len(retrieved_chunk_ids)
            if retrieved_chunk_ids
            else 0.0
        )

        # =====================================================
        # RECALL@K
        # =====================================================

        recall_at_k = (
            hit_groups
            / len(relevance_groups)
            if relevance_groups
            else 0.0
        )


        
        # =====================================================
        # HIT@K
        # =====================================================

        def compute_hit(k: int) -> float:
            return (
                1.0
                if any(
                    chunk_id
                    in relevant_chunk_ids
                    for chunk_id
                    in retrieved_chunk_ids[:k]
                )
                else 0.0
            )

        hit_at_1 = compute_hit(1)
        hit_at_3 = compute_hit(3)
        hit_at_5 = compute_hit(5)

        # =====================================================
        # FIRST RELEVANT RANK + RECIPROCAL RANK
        # =====================================================

        first_relevant_rank: int | None = None

        for rank, chunk_id in enumerate(
            retrieved_chunk_ids,
            start=1,
        ):
            if (
                chunk_id
                in relevant_chunk_ids
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

        retrieved_details = []

        for index, item in enumerate(
            retrieved_items,
            start=1,
        ):
            detail = {
                "rank":
                    index,

                "chunk_id":
                    item.chunk_id,

                "source":
                    item.source,

                "page":
                    item.page,

                "category":
                    item.category,

                "distance":
                    item.distance,

                "is_relevant":
                    item.chunk_id
                    in relevant_chunk_ids,

                "content_preview":
                    item.content[:250],
            }

            # =================================================
            # OPTIONAL BM25 SCORE
            # =================================================

            bm25_score = (
                item.metadata.get(
                    "bm25_score"
                )
                if item.metadata
                else None
            )

            if bm25_score is not None:
                detail[
                    "bm25_score"
                ] = bm25_score

            retrieved_details.append(
                detail
            )

            rrf_score = (
                item.metadata.get(
                    "rrf_score"
                )
                if item.metadata
                else None
            )

            if rrf_score is not None:
                detail[
                    "rrf_score"
                ] = rrf_score

            dense_rank = (
                item.metadata.get(
                    "dense_rank"
                )
                if item.metadata
                else None
            )

            if dense_rank is not None:
                detail[
                    "dense_rank"
                ] = dense_rank

            bm25_rank = (
                item.metadata.get(
                    "bm25_rank"
                )
                if item.metadata
                else None
            )

            if bm25_rank is not None:
                detail[
                    "bm25_rank"
                ] = bm25_rank

        # =====================================================
        # PER-QUERY RESULT
        # =====================================================

        return {
            "question_id":
                question_id,

            "question":
                question,

            "category":
                category,

            "retrieval_mode":
                mode,

            "top_k":
                top_k,

            "reference_chunk_ids":
                sorted(
                    original_reference_chunk_ids
                ),

            "relevant_chunk_ids":
                sorted(
                    relevant_chunk_ids
                ),

            "relevance_groups":
                [
                    sorted(group)
                    for group in relevance_groups
                ],

            "retrieved_chunk_ids":
                retrieved_chunk_ids,

            "relevant_retrieved_ids":
                sorted(
                    relevant_retrieved
                ),

            "relevant_count":
                relevant_count,

            "precision_at_5":
                precision_at_k,

            "recall_at_5":
                recall_at_k,

            "hit_at_1":
                hit_at_1,

            "hit_at_3":
                hit_at_3,

            "hit_at_5":
                hit_at_5,

            "first_relevant_rank":
                first_relevant_rank,

            "reciprocal_rank":
                reciprocal_rank,

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

        if mode not in self.VALID_MODES:
            raise ValueError(
                "mode phải là một trong: "
                f"{sorted(self.VALID_MODES)}"
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
                        question_index=index,
                    )
                )

                results.append(
                    case_result
                )

            except ValueError as error:
                skipped_cases.append(
                    {
                        "question_id":
                            index,

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

                "top_k":
                    top_k,

                "benchmark_file":
                    self.test_file.name,

                "total_cases":
                    len(test_cases),

                "evaluated_cases":
                    0,

                "skipped_cases":
                    len(skipped_cases),

                "metrics": {
                    "precision_at_5":
                        0.0,

                    "recall_at_5":
                        0.0,

                    "hit_at_1":
                        0.0,

                    "hit_at_3":
                        0.0,

                    "hit_at_5":
                        0.0,

                    "mrr":
                        0.0,
                },

                "category_summary":
                    {},

                "per_query":
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
                item["precision_at_5"]
                for item in results
            )
            / evaluated_count
        )

        mean_recall = (
            sum(
                item["recall_at_5"]
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
                item["reciprocal_rank"]
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

            category_stats.setdefault(
                category,
                [],
            )

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

                "precision_at_5":
                    sum(
                        item["precision_at_5"]
                        for item in items
                    )
                    / count,

                "recall_at_5":
                    sum(
                        item["recall_at_5"]
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
                        item["reciprocal_rank"]
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

            "top_k":
                top_k,

            "benchmark_file":
                self.test_file.name,

            "total_cases":
                len(test_cases),

            "evaluated_cases":
                evaluated_count,

            "skipped_cases":
                len(skipped_cases),

            "metrics": {
                "precision_at_5":
                    mean_precision,

                "recall_at_5":
                    mean_recall,

                "hit_at_1":
                    mean_hit_at_1,

                "hit_at_3":
                    mean_hit_at_3,

                "hit_at_5":
                    mean_hit_at_5,

                "mrr":
                    mean_mrr,
            },

            "category_summary":
                category_summary,

            "per_query":
                results,

            "skipped":
                skipped_cases,
        }

    # =========================================================
    # SAVE RESULT
    # =========================================================

    def save_result(
        self,
        result: dict[str, Any],
    ) -> Path:
        """
        Lưu kết quả evaluation ra JSON.

        Mỗi retrieval mode có một file riêng.
        """

        mode = str(
            result.get(
                "retrieval_mode",
                "unknown",
            )
        )

        output_file = (
            self.results_dir
            / f"{mode}_results.json"
        )

        output_file.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return output_file


# =============================================================
# PRINT SUMMARY
# =============================================================


def print_evaluation_summary(
    result: dict[str, Any],
) -> None:
    """
    In summary của benchmark.
    """

    metrics = result.get(
        "metrics",
        {},
    )

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
        "Benchmark:",
        result.get(
            "benchmark_file",
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
        f'{metrics.get("precision_at_5", 0.0) * 100:.2f}%',
    )

    print(
        "Recall@5:",
        f'{metrics.get("recall_at_5", 0.0) * 100:.2f}%',
    )

    print(
        "Hit@1:",
        f'{metrics.get("hit_at_1", 0.0) * 100:.2f}%',
    )

    print(
        "Hit@3:",
        f'{metrics.get("hit_at_3", 0.0) * 100:.2f}%',
    )

    print(
        "Hit@5:",
        f'{metrics.get("hit_at_5", 0.0) * 100:.2f}%',
    )

    print(
        "MRR:",
        f'{metrics.get("mrr", 0.0):.4f}',
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
            f'{stats["precision_at_5"] * 100:.2f}%',
        )

        print(
            "Recall@5:",
            f'{stats["recall_at_5"] * 100:.2f}%',
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
        for item in result["per_query"]
        if item["hit_at_5"] == 0
    ]

    if not failed:
        print(
            "No failed cases."
        )

    else:
        for item in failed:
            print(
                "\nQuestion ID:",
                item["question_id"],
            )

            print(
                "Question:",
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
        for item in result["per_query"]
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
                "\nQuestion ID:",
                item["question_id"],
            )

            print(
                "Question:",
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
                "Recall@5:",
                f'{item["recall_at_5"] * 100:.2f}%',
            )

            print(
                "Reciprocal rank:",
                f'{item["reciprocal_rank"]:.4f}',
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

                if (
                    detail.get(
                        "bm25_score"
                    )
                    is not None
                ):
                    print(
                        "    BM25 score:",
                        detail[
                            "bm25_score"
                        ],
                    )

                if (
                    detail.get(
                        "distance"
                    )
                    is not None
                ):
                    print(
                        "    Distance:",
                        detail[
                            "distance"
                        ],
                    )

                print(
                    "    Preview:",
                    detail[
                        "content_preview"
                    ],
                )


# =============================================================
# RUN ONE EXPERIMENT
# =============================================================


def run_experiment(
    service: IDRetrievalEvaluation,
    mode: str,
    title: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Chạy một retrieval configuration,
    in summary và lưu JSON.
    """

    print(
        "\n"
        "========================================"
    )

    print(
        title
    )

    print(
        "========================================"
    )

    result = service.evaluate(
        top_k=top_k,
        mode=mode,
    )

    print_evaluation_summary(
        result
    )

    output_file = (
        service.save_result(
            result
        )
    )

    print(
        "\nSaved result:",
        output_file,
    )

    return result


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

    run_experiment(
        service=service,
        mode="baseline",
        title=(
            "EXPERIMENT 1: "
            "SEMANTIC-ONLY BASELINE"
        ),
        top_k=5,
    )

    # =========================================================
    # EXPERIMENT 2
    # BM25 BASELINE
    # =========================================================

    run_experiment(
        service=service,
        mode="bm25",
        title=(
            "EXPERIMENT 2: "
            "BM25 BASELINE"
        ),
        top_k=5,
    )

    # =========================================================
    # EXPERIMENT 3
    # SEMANTIC + LEXICAL
    # =========================================================

    run_experiment(
        service=service,
        mode="semantic_lexical",
        title=(
            "EXPERIMENT 3: "
            "SEMANTIC + LEXICAL"
        ),
        top_k=5,
    )

    # =========================================================
    # EXPERIMENT 4
    # SEMANTIC + LEXICAL + PHRASE BOOST
    # =========================================================

    run_experiment(
        service=service,
        mode="optimized",
        title=(
            "EXPERIMENT 4: "
            "SEMANTIC + LEXICAL "
            "+ PHRASE BOOST"
        ),
        top_k=5,
    )

    run_experiment(
        service=service,
        mode="hybrid_rrf",
        title=(
            "EXPERIMENT 3: "
            "HYBRID DENSE + BM25 (RRF)"
        ),
        top_k=5,
    )