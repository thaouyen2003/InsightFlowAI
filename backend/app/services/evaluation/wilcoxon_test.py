import json
from pathlib import Path
from itertools import combinations

from scipy.stats import wilcoxon


RESULTS_DIR = Path(
    "app/services/evaluation/results"
)

FILES = {
    "BM25": RESULTS_DIR / "bm25_results.json",
    "Semantic-only": RESULTS_DIR / "baseline_results.json",
    "Hybrid RRF": RESULTS_DIR / "hybrid_rrf_results.json",
    "Semantic + Lexical": RESULTS_DIR / "semantic_lexical_results.json",
    "Full Reranking": RESULTS_DIR / "optimized_results.json",
}


def load_per_query(path: Path):
    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        raise ValueError(
            f"{path.name} không có JSON object ở root."
        )

    rows = data.get("per_query", [])

    return {
        str(row["question_id"]): row
        for row in rows
    }


def compare(
    name_a,
    data_a,
    name_b,
    data_b,
    metric,
):
    common_ids = sorted(
        set(data_a) & set(data_b),
        key=lambda x: int(x)
        if x.isdigit()
        else x,
    )

    x = [
        float(data_a[qid][metric])
        for qid in common_ids
    ]

    y = [
        float(data_b[qid][metric])
        for qid in common_ids
    ]

    differences = [
        b - a
        for a, b in zip(x, y)
    ]

    nonzero = sum(
        1
        for d in differences
        if d != 0
    )

    improved = sum(
        1
        for d in differences
        if d > 0
    )

    degraded = sum(
        1
        for d in differences
        if d < 0
    )

    tied = len(differences) - nonzero

    if nonzero == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        result = wilcoxon(
            x,
            y,
            zero_method="wilcox",
            alternative="two-sided",
            method="auto",
        )

        statistic = float(
            result.statistic
        )
        p_value = float(
            result.pvalue
        )

    print(
        f"\n{name_a} vs {name_b}"
    )
    print(
        f"Metric: {metric}"
    )
    print(
        f"N queries: {len(common_ids)}"
    )
    print(
        f"Improved in {name_b}: {improved}"
    )
    print(
        f"Degraded in {name_b}: {degraded}"
    )
    print(
        f"Ties: {tied}"
    )
    print(
        f"Wilcoxon W: {statistic:.4f}"
    )
    print(
        f"p-value: {p_value:.6f}"
    )
    print(
        "Significant at alpha=0.05:",
        "YES" if p_value < 0.05 else "NO",
    )


datasets = {
    name: load_per_query(path)
    for name, path in FILES.items()
}

# MRR is derived from per-query reciprocal rank.
metric = "reciprocal_rank"

comparisons = [
    ("BM25", "Semantic-only"),
    ("BM25", "Hybrid RRF"),
    ("Semantic-only", "Hybrid RRF"),
    ("Semantic-only", "Semantic + Lexical"),
    ("Semantic-only", "Full Reranking"),
    ("Semantic + Lexical", "Full Reranking"),
]

print(
    "========================================"
)
print(
    "WILCOXON SIGNED-RANK TEST"
)
print(
    "Per-query reciprocal rank"
)
print(
    "========================================"
)

for name_a, name_b in comparisons:
    compare(
        name_a,
        datasets[name_a],
        name_b,
        datasets[name_b],
        metric,
    )
