import json
from itertools import combinations
from pathlib import Path

from scipy.stats import wilcoxon


RESULTS_DIR = (
    Path(__file__)
    .resolve()
    .parent
    / "results"
)


FILES = {
    "semantic": (
        RESULTS_DIR
        / "baseline_results.json"
    ),
    "bm25": (
        RESULTS_DIR
        / "bm25_results.json"
    ),
    "hybrid_rrf": (
        RESULTS_DIR
        / "hybrid_rrf_results.json"
    ),
    "semantic_lexical": (
        RESULTS_DIR
        / "semantic_lexical_results.json"
    ),
    "optimized": (
        RESULTS_DIR
        / "optimized_results.json"
    ),
}


def load_rr(
    path: Path,
) -> dict[int, float]:
    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    result: dict[int, float] = {}

    for row in data["per_query"]:
        question_id = int(
            row["question_id"]
        )

        result[
            question_id
        ] = float(
            row[
                "reciprocal_rank"
            ]
        )

    return result


def compare(
    name_a: str,
    rr_a: dict[int, float],
    name_b: str,
    rr_b: dict[int, float],
) -> dict:
    common_ids = sorted(
        set(rr_a)
        & set(rr_b)
    )

    values_a = [
        rr_a[qid]
        for qid in common_ids
    ]

    values_b = [
        rr_b[qid]
        for qid in common_ids
    ]

    differences = [
        a - b
        for a, b in zip(
            values_a,
            values_b,
            strict=True,
        )
    ]

    changed = sum(
        1
        for value in differences
        if value != 0
    )

    if changed == 0:
        statistic = 0.0
        p_value = 1.0

    else:
        statistic, p_value = wilcoxon(
            values_a,
            values_b,
            zero_method="zsplit",
            alternative="two-sided",
        )

    return {
        "configuration_a":
            name_a,

        "configuration_b":
            name_b,

        "n_queries":
            len(common_ids),

        "changed_queries":
            changed,

        "mean_rr_a":
            sum(values_a)
            / len(values_a),

        "mean_rr_b":
            sum(values_b)
            / len(values_b),

        "wilcoxon_statistic":
            float(statistic),

        "p_value":
            float(p_value),

        "significant_at_0_05":
            bool(
                p_value < 0.05
            ),
    }


def main() -> None:
    all_rr = {
        name: load_rr(path)
        for name, path in FILES.items()
    }

    comparisons = []

    for name_a, name_b in combinations(
        all_rr.keys(),
        2,
    ):
        result = compare(
            name_a,
            all_rr[name_a],
            name_b,
            all_rr[name_b],
        )

        comparisons.append(
            result
        )

        print(
            f"\n{name_a} "
            f"vs "
            f"{name_b}"
        )

        print(
            "N:",
            result[
                "n_queries"
            ],
        )

        print(
            "Changed queries:",
            result[
                "changed_queries"
            ],
        )

        print(
            "Mean RR A:",
            round(
                result[
                    "mean_rr_a"
                ],
                4,
            ),
        )

        print(
            "Mean RR B:",
            round(
                result[
                    "mean_rr_b"
                ],
                4,
            ),
        )

        print(
            "Statistic:",
            round(
                result[
                    "wilcoxon_statistic"
                ],
                4,
            ),
        )

        print(
            "p-value:",
            round(
                result[
                    "p_value"
                ],
                6,
            ),
        )

        print(
            "Significant:",
            result[
                "significant_at_0_05"
            ],
        )

    output_file = (
        RESULTS_DIR
        / "wilcoxon_results.json"
    )

    output_file.write_text(
        json.dumps(
            comparisons,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\nSaved:",
        output_file,
    )


if __name__ == "__main__":
    main()