import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.services.rag.embedding_service import (
    EmbeddingService,
)
from app.services.rag.vector_store import (
    VectorStore,
)


# =============================================================
# CONFIGURATION
# =============================================================

CHUNKING_CONFIGS = {
    "chunk_400_75": {
        "collection_name":
            "vhu_knowledge_chunk_400_75",
        "chunk_size": 400,
        "chunk_overlap": 75,
        "expected_chunks": 326,
    },

    "chunk_800_150": {
        "collection_name":
            "vhu_knowledge_chunk_800_150",
        "chunk_size": 800,
        "chunk_overlap": 150,
        "expected_chunks": 169,
    },

    "chunk_1200_200": {
        "collection_name":
            "vhu_knowledge_chunk_1200_200",
        "chunk_size": 1200,
        "chunk_overlap": 200,
        # Chưa biết cho tới khi build hoàn tất.
        "expected_chunks": None,
    },
}


class ChunkingAblationEvaluation:
    """
    Đánh giá ảnh hưởng của chunk_size / chunk_overlap
    đối với semantic retrieval.

    Controlled variables:
    - cùng frozen corpus
    - cùng embedding model
    - cùng 50 benchmark questions
    - cùng category filtering
    - cùng Top-K
    - cùng semantic retrieval

    Independent variable:
    - chunk_size
    - chunk_overlap

    Metrics:
    - Precision@5
    - Recall@5
    - Hit@1
    - Hit@3
    - Hit@5
    - MRR
    """

    def __init__(
        self,
    ) -> None:

        self.evaluation_dir = (
            Path(__file__)
            .resolve()
            .parent
        )

        self.results_dir = (
            self.evaluation_dir
            / "results"
            / "chunking_ablation"
        )

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Ground truth FINAL theo từng chunk config.
        #
        # Không dùng candidate mapping trực tiếp.
        self.ground_truth_dir = (
            self.evaluation_dir
            / "chunking_ground_truth_final"
        )

        self.embedding_service = (
            EmbeddingService()
        )
        self.embedding_cache_file = (
            self.evaluation_dir
            / "query_embeddings_cache.json"
        )

        if self.embedding_cache_file.exists():
            self.embedding_cache = json.loads(
                self.embedding_cache_file.read_text(
                    encoding="utf-8"
                )
            )
        else:
            self.embedding_cache = {}

        self.stores: dict[
            str,
            VectorStore,
        ] = {}

        for (
            config_name,
            config,
        ) in CHUNKING_CONFIGS.items():

            self.stores[
                config_name
            ] = VectorStore(
                collection_name=
                    config[
                        "collection_name"
                    ]
            )

    # =========================================================
    # COLLECTION VALIDATION
    # =========================================================

    def validate_collections(
        self,
    ) -> None:
        """
        Không cho chạy evaluation nếu collection
        đang build dở.
        """

        print(
            "\n=== COLLECTION VALIDATION ==="
        )

        for (
            config_name,
            config,
        ) in CHUNKING_CONFIGS.items():

            store = self.stores[
                config_name
            ]

            actual_count = (
                store.count()
            )

            expected_count = (
                config[
                    "expected_chunks"
                ]
            )

            print(
                config_name,
                "=>",
                actual_count,
                "chunks",
            )

            if actual_count <= 0:
                raise RuntimeError(
                    f"{config_name} đang rỗng."
                )

            if (
                expected_count is not None
                and actual_count
                != expected_count
            ):
                raise RuntimeError(
                    f"{config_name} chưa hoàn chỉnh. "
                    f"Expected={expected_count}, "
                    f"actual={actual_count}"
                )

    # =========================================================
    # LOAD FINAL GROUND TRUTH
    # =========================================================

    def load_ground_truth(
        self,
        config_name: str,
    ) -> list[dict[str, Any]]:
        """
        Expected schema:

        [
          {
            "id": 1,
            "question": "...",
            "category": "...",
            "reference_chunk_ids": [...]
          }
        ]
        """

        path = (
            self.ground_truth_dir
            / f"{config_name}.json"
        )

        if not path.exists():
            raise FileNotFoundError(
                "Chưa có finalized ground truth "
                f"cho {config_name}: {path}"
            )

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            list,
        ):
            raise ValueError(
                f"{path.name} phải là list."
            )

        if len(data) != 50:
            raise RuntimeError(
                f"{config_name} phải có "
                f"50 benchmark cases, "
                f"actual={len(data)}"
            )

        return data

    # =========================================================
    # QUERY COLLECTION USING PRECOMPUTED EMBEDDING
    # =========================================================

    @staticmethod
    def search_with_embedding(
        store: VectorStore,
        query_embedding: list[float],
        top_k: int,
        category: str | None,
    ) -> list[dict[str, Any]]:
        """
        Semantic search trực tiếp bằng query embedding
        đã tạo sẵn.

        Nhờ vậy cùng một query vector được reuse
        giữa các chunking configurations.
        """

        if top_k <= 0:
            raise ValueError(
                "top_k phải > 0."
            )

        collection_count = (
            store.count()
        )

        if collection_count <= 0:
            return []

        effective_top_k = min(
            top_k,
            collection_count,
        )

        query_args: dict[
            str,
            Any,
        ] = {
            "query_embeddings": [
                query_embedding
            ],

            "n_results":
                effective_top_k,

            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        clean_category = (
            str(category).strip()
            if category
            else None
        )

        if clean_category:
            query_args["where"] = {
                "category":
                    clean_category
            }

        response = (
            store.collection.query(
                **query_args
            )
        )

        ids = (
            store._first_result_list(
                response.get(
                    "ids"
                )
            )
        )

        documents = (
            store._first_result_list(
                response.get(
                    "documents"
                )
            )
        )

        metadatas = (
            store._first_result_list(
                response.get(
                    "metadatas"
                )
            )
        )

        distances = (
            store._first_result_list(
                response.get(
                    "distances"
                )
            )
        )

        results = []

        for (
            chunk_id,
            content,
            metadata,
            distance,
        ) in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            results.append(
                {
                    "chunk_id":
                        str(chunk_id),

                    "content":
                        str(
                            content or ""
                        ).strip(),

                    "metadata":
                        dict(
                            metadata or {}
                        ),

                    "distance":
                        (
                            float(distance)
                            if distance
                            is not None
                            else None
                        ),
                }
            )

        results.sort(
            key=lambda item: (
                item[
                    "distance"
                ]
                if item[
                    "distance"
                ] is not None
                else float("inf")
            )
        )

        return results

    # =========================================================
    # RETRIEVE WITH FALLBACK
    # =========================================================

    def retrieve(
        self,
        config_name: str,
        query_embedding: list[float],
        category: str | None,
        top_k: int,
    ) -> list[dict[str, Any]]:

        store = self.stores[
            config_name
        ]

        results = (
            self.search_with_embedding(
                store=store,
                query_embedding=
                    query_embedding,
                top_k=top_k,
                category=category,
            )
        )

        # Giữ đúng behavior evaluator hiện tại:
        # nếu category filter không có kết quả,
        # fallback toàn corpus.
        if (
            not results
            and category is not None
        ):
            results = (
                self.search_with_embedding(
                    store=store,
                    query_embedding=
                        query_embedding,
                    top_k=top_k,
                    category=None,
                )
            )

        return results

    # =========================================================
    # METRICS FOR ONE CASE
    # =========================================================

    @staticmethod
    def compute_metrics(
        retrieved_ids: list[str],
        relevance_groups: list[set[str]],
    ) -> dict[str, Any]:

        retrieved_set = set(retrieved_ids)

        relevant_ids = set().union(
            *relevance_groups
        ) if relevance_groups else set()

        hit_groups = sum(
            1
            for group in relevance_groups
            if retrieved_set & group
        )

        precision = (
            hit_groups / len(retrieved_ids)
            if retrieved_ids
            else 0.0
        )

        recall = (
            hit_groups / len(relevance_groups)
            if relevance_groups
            else 0.0
        )

        def hit(k: int) -> float:
            return (
                1.0
                if any(
                    chunk_id in relevant_ids
                    for chunk_id in retrieved_ids[:k]
                )
                else 0.0
            )

        first_relevant_rank = None

        for rank, chunk_id in enumerate(
            retrieved_ids,
            start=1,
        ):
            if chunk_id in relevant_ids:
                first_relevant_rank = rank
                break

        reciprocal_rank = (
            1.0 / first_relevant_rank
            if first_relevant_rank
            else 0.0
        )

        return {
            "precision_at_5": precision,
            "recall_at_5": recall,
            "hit_at_1": hit(1),
            "hit_at_3": hit(3),
            "hit_at_5": hit(5),
            "first_relevant_rank": first_relevant_rank,
            "reciprocal_rank": reciprocal_rank,
            "relevant_retrieved_ids": sorted(
                retrieved_set & relevant_ids
            ),
        }

    
    # =========================================================
    # EVALUATE ALL CONFIGS
    # =========================================================

    def evaluate(
        self,
        top_k: int = 5,
    ) -> dict[str, Any]:

        self.validate_collections()

        # =====================================================
        # LOAD GT
        # =====================================================

        ground_truth = {
            config_name:
                self.load_ground_truth(
                    config_name
                )
            for config_name
            in CHUNKING_CONFIGS
        }

        # =====================================================
        # VERIFY QUESTION ALIGNMENT
        # =====================================================

        reference_cases = (
            ground_truth[
                "chunk_800_150"
            ]
        )

        for config_name, cases in (
            ground_truth.items()
        ):
            for index, (
                reference_case,
                case,
            ) in enumerate(
                zip(
                    reference_cases,
                    cases,
                    strict=True,
                ),
                start=1,
            ):
                if (
                    reference_case[
                        "question"
                    ]
                    != case[
                        "question"
                    ]
                ):
                    raise RuntimeError(
                        "Question alignment "
                        "mismatch tại "
                        f"{config_name}, "
                        f"index={index}"
                    )

        # =====================================================
        # RESULT CONTAINERS
        # =====================================================

        per_config_results: dict[
            str,
            list[dict[str, Any]],
        ] = {
            config_name: []
            for config_name
            in CHUNKING_CONFIGS
        }

        # =====================================================
        # RUN 50 QUESTIONS
        # =====================================================

        total_questions = len(
            reference_cases
        )

        for index, reference_case in (
            enumerate(
                reference_cases,
                start=1,
            )
        ):

            question = str(
                reference_case[
                    "question"
                ]
            ).strip()

            print(
                f"\n[CHUNKING EVAL] "
                f"{index}/{total_questions}: "
                f"{question}"
            )

            # ===============================================
            # EMBED QUERY ONCE
            # ===============================================

            cache_key = str(
                reference_case.get(
                    "id",
                    index,
                )
            )

            if cache_key in self.embedding_cache:
                query_embedding = (
                    self.embedding_cache[
                        cache_key
                    ]
                )
            else:
                query_embedding = (
                    self.embedding_service
                    .embed_query(
                        question
                    )
                )

                self.embedding_cache[
                    cache_key
                ] = query_embedding

                self.embedding_cache_file.write_text(
                    json.dumps(
                        self.embedding_cache,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            # ===============================================
            # REUSE SAME VECTOR FOR ALL CONFIGS
            # ===============================================

            for config_name in (
                CHUNKING_CONFIGS
            ):

                case = (
                    ground_truth[
                        config_name
                    ][
                        index - 1
                    ]
                )

                category = (
                    case.get(
                        "category"
                    )
                )

                raw_groups = case.get(
                    "relevance_groups"
                )

                if raw_groups:
                    relevance_groups = [
                        {
                            str(chunk_id)
                            for chunk_id in group
                        }
                        for group in raw_groups
                    ]
                else:
                    relevance_groups = [
                        {
                            str(chunk_id)
                        }
                        for chunk_id in case.get(
                            "reference_chunk_ids",
                            []
                        )
                    ]

                if not relevance_groups:
                    raise RuntimeError(
                        "Missing relevance groups: "
                        f"{config_name}, "
                        f"question={index}"
                    )

                relevant_ids = set().union(
                    *relevance_groups
                )

                

                retrieved = (
                    self.retrieve(
                        config_name=
                            config_name,

                        query_embedding=
                            query_embedding,

                        category=
                            category,

                        top_k=
                            top_k,
                    )
                )

                retrieved_ids = [
                    item[
                        "chunk_id"
                    ]
                    for item in retrieved
                ]

                metrics = (
                    self.compute_metrics(
                        retrieved_ids=
                            retrieved_ids,

                        relevance_groups=
                            relevance_groups,
                    )
                )

                per_config_results[
                    config_name
                ].append(
                    {
                        "id":
                            case.get(
                                "id",
                                index,
                            ),

                        "question":
                            question,

                        "category":
                            category,

                        "reference_chunk_ids":
                            sorted(
                                relevant_ids
                            ),

                        "relevance_groups": [
                            sorted(group)
                            for group in relevance_groups
                        ],
                        "retrieved_chunk_ids":
                            retrieved_ids,

                        **metrics,

                        "retrieved_details": [
                            {
                                "rank":
                                    rank,

                                "chunk_id":
                                    item[
                                        "chunk_id"
                                    ],

                                "source":
                                    item[
                                        "metadata"
                                    ].get(
                                        "source"
                                    ),

                                "page":
                                    item[
                                        "metadata"
                                    ].get(
                                        "page"
                                    ),

                                "distance":
                                    item[
                                        "distance"
                                    ],

                                "is_relevant":
                                    item[
                                        "chunk_id"
                                    ]
                                    in relevant_ids,

                                "content_preview":
                                    item[
                                        "content"
                                    ][:300],
                            }
                            for rank, item
                            in enumerate(
                                retrieved,
                                start=1,
                            )
                        ],
                    }
                )

        # =====================================================
        # SUMMARIZE
        # =====================================================

        config_summaries = {}

        for (
            config_name,
            results,
        ) in per_config_results.items():

            config_summaries[
                config_name
            ] = self.summarize(
                config_name=
                    config_name,
                results=results,
                top_k=top_k,
            )

        return {
            "experiment":
                "chunking_ablation",

            "retrieval":
                "semantic_only",

            "top_k":
                top_k,

            "questions":
                total_questions,

            "configs":
                config_summaries,
        }

    # =========================================================
    # SUMMARY
    # =========================================================

    def summarize(
        self,
        config_name: str,
        results: list[
            dict[str, Any]
        ],
        top_k: int,
    ) -> dict[str, Any]:

        count = len(
            results
        )

        if count == 0:
            raise RuntimeError(
                "Không có evaluation results."
            )

        def avg(
            field: str,
        ) -> float:
            return (
                sum(
                    float(
                        item[field]
                    )
                    for item in results
                )
                / count
            )

        # =====================================================
        # DOMAIN SUMMARY
        # =====================================================

        domain_groups: dict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        for item in results:
            domain_groups[
                item.get(
                    "category"
                )
                or "unknown"
            ].append(
                item
            )

        domain_summary = {}

        for (
            domain,
            items,
        ) in domain_groups.items():

            n = len(
                items
            )

            domain_summary[
                domain
            ] = {
                "questions":
                    n,

                "precision_at_5":
                    sum(
                        item[
                            "precision_at_5"
                        ]
                        for item in items
                    )
                    / n,

                "recall_at_5":
                    sum(
                        item[
                            "recall_at_5"
                        ]
                        for item in items
                    )
                    / n,

                "hit_at_1":
                    sum(
                        item[
                            "hit_at_1"
                        ]
                        for item in items
                    )
                    / n,

                "hit_at_3":
                    sum(
                        item[
                            "hit_at_3"
                        ]
                        for item in items
                    )
                    / n,

                "hit_at_5":
                    sum(
                        item[
                            "hit_at_5"
                        ]
                        for item in items
                    )
                    / n,

                "mrr":
                    sum(
                        item[
                            "reciprocal_rank"
                        ]
                        for item in items
                    )
                    / n,
            }

        config = (
            CHUNKING_CONFIGS[
                config_name
            ]
        )

        return {
            "collection_name":
                config[
                    "collection_name"
                ],

            "chunk_size":
                config[
                    "chunk_size"
                ],

            "chunk_overlap":
                config[
                    "chunk_overlap"
                ],

            "chunk_count":
                self.stores[
                    config_name
                ].count(),

            "questions":
                count,

            "metrics": {
                "precision_at_5":
                    avg(
                        "precision_at_5"
                    ),

                "recall_at_5":
                    avg(
                        "recall_at_5"
                    ),

                "hit_at_1":
                    avg(
                        "hit_at_1"
                    ),

                "hit_at_3":
                    avg(
                        "hit_at_3"
                    ),

                "hit_at_5":
                    avg(
                        "hit_at_5"
                    ),

                "mrr":
                    avg(
                        "reciprocal_rank"
                    ),
            },

            "domain_summary":
                domain_summary,

            "per_query":
                results,
        }

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        result: dict[str, Any],
    ) -> Path:

        output_file = (
            self.results_dir
            / "chunking_ablation_results.json"
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


def print_summary(
    result: dict[str, Any],
) -> None:

    print(
        "\n"
        "========================================"
    )

    print(
        "CHUNKING ABLATION RESULTS"
    )

    print(
        "========================================"
    )

    print(
        "\n"
        "Chunking | Chunks | "
        "P@5 | R@5 | "
        "Hit@1 | Hit@3 | Hit@5 | MRR"
    )

    for (
        config_name,
        summary,
    ) in result[
        "configs"
    ].items():

        metrics = (
            summary[
                "metrics"
            ]
        )

        label = (
            f'{summary["chunk_size"]}/'
            f'{summary["chunk_overlap"]}'
        )

        print(
            f'{label} | '
            f'{summary["chunk_count"]} | '
            f'{metrics["precision_at_5"]:.4f} | '
            f'{metrics["recall_at_5"]:.4f} | '
            f'{metrics["hit_at_1"]:.4f} | '
            f'{metrics["hit_at_3"]:.4f} | '
            f'{metrics["hit_at_5"]:.4f} | '
            f'{metrics["mrr"]:.4f}'
        )

    print(
        "\n=== DOMAIN MRR ==="
    )

    for (
        config_name,
        summary,
    ) in result[
        "configs"
    ].items():

        print(
            "\n",
            config_name,
        )

        for (
            domain,
            stats,
        ) in summary[
            "domain_summary"
        ].items():

            print(
                domain,
                "=>",
                f'MRR={stats["mrr"]:.4f}',
                f'Hit@1={stats["hit_at_1"]:.4f}',
                f'R@5={stats["recall_at_5"]:.4f}',
            )


# =============================================================
# MAIN
# =============================================================


if __name__ == "__main__":

    evaluator = (
        ChunkingAblationEvaluation()
    )

    result = evaluator.evaluate(
        top_k=5
    )

    print_summary(
        result
    )

    output_file = (
        evaluator.save(
            result
        )
    )

    print(
        "\nSaved:",
        output_file,
    )