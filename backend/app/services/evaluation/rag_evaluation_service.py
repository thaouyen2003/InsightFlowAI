import json
from pathlib import Path
from typing import Any

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

from app.services.rag.rag_service import RAGService
from app.services.rag.retriever import KnowledgeRetriever


class RAGEvaluationService:
    def __init__(self) -> None:
        self.rag_service = RAGService()
        self.retriever = KnowledgeRetriever()

        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        self.test_file = (
            backend_dir
            / "database"
            / "evaluation"
            / "rag_test_cases.json"
        )

    def load_test_cases(
        self,
    ) -> list[dict[str, Any]]:
        """
        Đọc bộ câu hỏi benchmark RAG.
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

        if not isinstance(data, list):
            raise ValueError(
                "rag_test_cases.json phải là một danh sách."
            )

        return data

    def build_evaluation_dataset(
        self,
        limit: int | None = None,
        top_k: int = 5,
    ) -> Dataset:
        """
        Chạy RAG trên test cases và tạo dataset
        theo format RAGAS 0.3.x.
        """

        test_cases = self.load_test_cases()

        if limit is not None:
            test_cases = test_cases[:limit]

        questions: list[str] = []
        answers: list[str] = []
        contexts: list[list[str]] = []
        ground_truths: list[str] = []
        reference_contexts_list: list[list[str]] = []

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

            category = test_case.get(
                "category"
            )

            reference = str(
                test_case.get(
                    "reference",
                    "",
                )
            ).strip()
            reference_contexts = test_case.get(
                "reference_contexts",
                []
            )

            if not isinstance(
                reference_contexts,
                list,
            ):
                raise ValueError(
                    f"Test case {index} reference_contexts "
                    "phải là list."
                )

            reference_contexts = [
                str(item).strip()
                for item in reference_contexts
                if str(item).strip()
            ]



            if not question:
                raise ValueError(
                    f"Test case {index} thiếu question."
                )

            if not reference:
                raise ValueError(
                    f"Test case {index} thiếu reference."
                )

            print(
                f"[RAG EVAL] Running "
                f"{index}/{len(test_cases)}: "
                f"{question}"
            )

            # 1. Lấy câu trả lời thực tế từ RAG
            rag_result = self.rag_service.ask(
                question=question,
                top_k=top_k,
                category=category,
            )

            # 2. Lấy chính các context từ retriever
            retrieved_items = (
                self.retriever.retrieve(
                    query=question,
                    top_k=top_k,
                    category=category,
                )
            )

            # Giống logic fallback của RAGService
            if (
                not retrieved_items
                and category is not None
            ):
                retrieved_items = (
                    self.retriever.retrieve(
                        query=question,
                        top_k=top_k,
                        category=None,
                    )
                )

            retrieved_contexts = [
                item.content
                for item in retrieved_items
            ]

            questions.append(
                question
            )

            answers.append(
                rag_result.answer
            )

            contexts.append(
                retrieved_contexts
            )

            ground_truths.append(
                reference
            )

            reference_contexts_list.append(
                reference_contexts
            )

        return Dataset.from_dict(
            {
                "question": questions,
                "answer": answers,
                "contexts": contexts,
                "ground_truth": ground_truths,
                "reference_contexts":
                    reference_contexts_list,
            }
        )

    def evaluate(
        self,
        limit: int | None = None,
        top_k: int = 5,
    ):
        """
        Chạy benchmark RAGAS.
        """

        dataset = (
            self.build_evaluation_dataset(
                limit=limit,
                top_k=top_k,
            )
        )

        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
        )

        return result