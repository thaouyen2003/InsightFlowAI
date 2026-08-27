from ragas.metrics import (
    NonLLMStringSimilarity,
)

from ragas.dataset_schema import (
    SingleTurnSample,
)

from app.services.evaluation.rag_evaluation_service import (
    RAGEvaluationService,
)


service = RAGEvaluationService()

dataset = service.build_evaluation_dataset(
    limit=1,
    top_k=5,
)

row = dataset[0]

reference_context = row[
    "reference_contexts"
][0]

metric = NonLLMStringSimilarity()


print("\n=== REFERENCE CONTEXT ===")
print(reference_context)


for index, context in enumerate(
    row["contexts"],
    start=1,
):
    sample = SingleTurnSample(
        reference=reference_context,
        response=context,
    )

    score = metric.single_turn_score(
        sample
    )

    print(
        f"\nContext {index}: "
        f"{score:.4f} "
        f"({score * 100:.2f}%)"
    )

    print(
        context[:250]
    )