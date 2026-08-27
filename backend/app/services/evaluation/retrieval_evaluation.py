from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import (
    NonLLMContextPrecisionWithReference,
)

from app.services.evaluation.rag_evaluation_service import (
    RAGEvaluationService,
)


def run_retrieval_evaluation() -> None:
    service = RAGEvaluationService()

    dataset = service.build_evaluation_dataset(
        limit=1,
        top_k=5,
    )

    row = dataset[0]

    metric = (
        NonLLMContextPrecisionWithReference()
    )

    sample = SingleTurnSample(
        reference_contexts=row[
            "reference_contexts"
        ],
        retrieved_contexts=row[
            "contexts"
        ],
    )

    score = metric.single_turn_score(
        sample
    )

    print(
        "\n=== RETRIEVAL EVALUATION ==="
    )

    print(
        "Context Precision:",
        round(score, 4),
    )

    print(
        "Context Precision (%):",
        f"{score * 100:.2f}%",
    )


if __name__ == "__main__":
    run_retrieval_evaluation()