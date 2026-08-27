import re
import unicodedata
from typing import List, Dict, Any


class AnswerEvaluator:
    """
    Simple deterministic evaluator for RAG-generated answers.

    Evaluation method:
    - Normalize generated answer and ground-truth keywords.
    - Check how many expected keywords/facts appear in the answer.
    - Calculate Answer Keyword Coverage.
    - Classify answer as:
        + correct
        + partially_correct
        + incorrect

    This evaluator does NOT use:
    - Gemini
    - RAGAS
    - LLM-as-a-Judge

    Therefore, it does not consume LLM quota.
    """

    def __init__(
        self,
        correct_threshold: float = 0.8,
        partial_threshold: float = 0.5,
    ):
        self.correct_threshold = correct_threshold
        self.partial_threshold = partial_threshold

    # ============================================================
    # TEXT NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize Vietnamese/English text for keyword matching.

        Example:
            "Điểm Trung Bình Tích Lũy"
        becomes:
            "diem trung binh tich luy"
        """

        if not text:
            return ""

        text = str(text).lower().strip()

        # Convert Đ/đ manually because Unicode decomposition
        # does not always normalize it as expected.
        text = text.replace("đ", "d")

        # Remove Vietnamese accents
        text = unicodedata.normalize("NFD", text)

        text = "".join(
            char
            for char in text
            if unicodedata.category(char) != "Mn"
        )

        # Standardize decimal comma:
        # 2,00 -> 2.00
        text = re.sub(
            r"(\d),(\d)",
            r"\1.\2",
            text,
        )

        # Remove unnecessary punctuation but preserve
        # useful characters such as '.', '/', '%', '-', '>'
        text = re.sub(
            r"[^\w\s./%><=-]",
            " ",
            text,
        )

        # Normalize spaces
        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text

    # ============================================================
    # KEYWORD MATCHING
    # ============================================================

    def keyword_exists(
        self,
        generated_answer: str,
        keyword: str,
    ) -> bool:
        """
        Check whether a keyword/fact exists in generated answer.
        """

        normalized_answer = self.normalize_text(
            generated_answer
        )

        normalized_keyword = self.normalize_text(
            keyword
        )

        if not normalized_keyword:
            return False

        return normalized_keyword in normalized_answer

    # ============================================================
    # SINGLE ANSWER EVALUATION
    # ============================================================

    def evaluate(
        self,
        generated_answer: str,
        answer_keywords: List[str],
        expected_answer: str | None = None,
        question: str | None = None,
    ) -> Dict[str, Any]:
        """
        Evaluate one generated answer.

        Score:
            matched keywords / total expected keywords

        Labels:
            score >= 0.8:
                correct

            score >= 0.5:
                partially_correct

            score < 0.5:
                incorrect
        """

        generated_answer = generated_answer or ""

        answer_keywords = answer_keywords or []

        matched_keywords: List[str] = []
        missing_keywords: List[str] = []

        # --------------------------------------------------------
        # Match expected facts
        # --------------------------------------------------------

        for keyword in answer_keywords:

            if self.keyword_exists(
                generated_answer,
                keyword,
            ):
                matched_keywords.append(keyword)

            else:
                missing_keywords.append(keyword)

        total_keywords = len(answer_keywords)

        matched_count = len(matched_keywords)

        # --------------------------------------------------------
        # Calculate score
        # --------------------------------------------------------

        if total_keywords == 0:
            score = 0.0

        else:
            score = matched_count / total_keywords

        score = round(score, 4)

        # --------------------------------------------------------
        # Determine label
        # --------------------------------------------------------

        if total_keywords == 0:
            label = "not_evaluable"

        elif score >= self.correct_threshold:
            label = "correct"

        elif score >= self.partial_threshold:
            label = "partially_correct"

        else:
            label = "incorrect"

        passed = label == "correct"

        # --------------------------------------------------------
        # Result
        # --------------------------------------------------------

        return {
            "question": question,

            "generated_answer": generated_answer,

            "expected_answer": expected_answer,

            "answer_keywords": answer_keywords,

            "matched_keywords": matched_keywords,

            "missing_keywords": missing_keywords,

            "matched_count": matched_count,

            "total_keywords": total_keywords,

            "score": score,

            "percentage": round(
                score * 100,
                2,
            ),

            "label": label,

            "passed": passed,
        }

    # ============================================================
    # BATCH EVALUATION
    # ============================================================

    def evaluate_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate multiple generated answers.

        Expected item format:

        {
            "question": "...",

            "generated_answer": "...",

            "expected_answer": "...",

            "answer_keywords": [
                "...",
                "..."
            ]
        }
        """

        results: List[Dict[str, Any]] = []

        for item in items:

            result = self.evaluate(
                question=item.get(
                    "question"
                ),

                generated_answer=item.get(
                    "generated_answer",
                    "",
                ),

                expected_answer=item.get(
                    "expected_answer"
                ),

                answer_keywords=item.get(
                    "answer_keywords",
                    [],
                ),
            )

            results.append(result)

        summary = self.build_summary(
            results
        )

        return {
            "summary": summary,
            "results": results,
        }

    # ============================================================
    # SUMMARY
    # ============================================================

    @staticmethod
    def build_summary(
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        total = len(results)

        if total == 0:
            return {
                "total_questions": 0,
                "correct": 0,
                "partially_correct": 0,
                "incorrect": 0,
                "not_evaluable": 0,
                "average_answer_score": 0.0,
                "correct_rate": 0.0,
                "partial_correct_rate": 0.0,
                "incorrect_rate": 0.0,
            }

        correct = sum(
            1
            for result in results
            if result["label"] == "correct"
        )

        partially_correct = sum(
            1
            for result in results
            if result["label"]
            == "partially_correct"
        )

        incorrect = sum(
            1
            for result in results
            if result["label"] == "incorrect"
        )

        not_evaluable = sum(
            1
            for result in results
            if result["label"]
            == "not_evaluable"
        )

        evaluable_results = [
            result
            for result in results
            if result["label"]
            != "not_evaluable"
        ]

        evaluable_count = len(
            evaluable_results
        )

        # --------------------------------------------------------
        # Average Answer Keyword Coverage
        # --------------------------------------------------------

        if evaluable_count == 0:
            average_score = 0.0

        else:
            average_score = sum(
                result["score"]
                for result
                in evaluable_results
            ) / evaluable_count

        # --------------------------------------------------------
        # Rates
        # --------------------------------------------------------

        if evaluable_count == 0:

            correct_rate = 0.0
            partial_rate = 0.0
            incorrect_rate = 0.0

        else:

            correct_rate = (
                correct
                / evaluable_count
            )

            partial_rate = (
                partially_correct
                / evaluable_count
            )

            incorrect_rate = (
                incorrect
                / evaluable_count
            )

        return {
            "total_questions": total,

            "evaluable_questions":
                evaluable_count,

            "correct": correct,

            "partially_correct":
                partially_correct,

            "incorrect": incorrect,

            "not_evaluable":
                not_evaluable,

            "average_answer_score":
                round(
                    average_score,
                    4,
                ),

            "average_answer_percentage":
                round(
                    average_score * 100,
                    2,
                ),

            "correct_rate":
                round(
                    correct_rate,
                    4,
                ),

            "correct_rate_percentage":
                round(
                    correct_rate * 100,
                    2,
                ),

            "partial_correct_rate":
                round(
                    partial_rate,
                    4,
                ),

            "partial_correct_rate_percentage":
                round(
                    partial_rate * 100,
                    2,
                ),

            "incorrect_rate":
                round(
                    incorrect_rate,
                    4,
                ),

            "incorrect_rate_percentage":
                round(
                    incorrect_rate * 100,
                    2,
                ),
        }


# ================================================================
# HELPER FUNCTION
# ================================================================

def evaluate_answer(
    generated_answer: str,
    answer_keywords: List[str],
    expected_answer: str | None = None,
    question: str | None = None,
) -> Dict[str, Any]:
    """
    Convenience function if you do not want
    to instantiate AnswerEvaluator manually.
    """

    evaluator = AnswerEvaluator()

    return evaluator.evaluate(
        question=question,

        generated_answer=generated_answer,

        expected_answer=expected_answer,

        answer_keywords=answer_keywords,
    )


# ================================================================
# LOCAL TEST
# ================================================================

if __name__ == "__main__":

    evaluator = AnswerEvaluator()

    # ------------------------------------------------------------
    # TEST 1
    # ------------------------------------------------------------

    test_answer_1 = """
    Sinh viên được xét tốt nghiệp khi có
    điểm trung bình tích lũy toàn khóa
    (CPA) từ 2.00/4.00 trở lên.
    """

    result_1 = evaluator.evaluate(
        question=(
            "Sinh viên cần CPA tối thiểu "
            "bao nhiêu để được xét tốt nghiệp?"
        ),

        generated_answer=test_answer_1,

        expected_answer=(
            "Sinh viên phải có CPA "
            "từ 2.00/4.00 trở lên."
        ),

        answer_keywords=[
            "CPA",
            "2.00",
        ],
    )

    print(
        "\n"
        "========================================"
    )

    print(
        "ANSWER EVALUATION TEST 1"
    )

    print(
        "========================================"
    )

    print(
        f"Question: "
        f"{result_1['question']}"
    )

    print(
        f"Generated Answer: "
        f"{result_1['generated_answer']}"
    )

    print(
        f"Expected Answer: "
        f"{result_1['expected_answer']}"
    )

    print(
        f"Matched: "
        f"{result_1['matched_keywords']}"
    )

    print(
        f"Missing: "
        f"{result_1['missing_keywords']}"
    )

    print(
        f"Score: "
        f"{result_1['score']}"
    )

    print(
        f"Percentage: "
        f"{result_1['percentage']}%"
    )

    print(
        f"Label: "
        f"{result_1['label']}"
    )

    # ------------------------------------------------------------
    # TEST BATCH
    # ------------------------------------------------------------

    test_items = [
        {
            "question":
                "Sinh viên cần CPA tối thiểu "
                "bao nhiêu để tốt nghiệp?",

            "generated_answer":
                "Sinh viên cần CPA từ "
                "2.00/4.00 trở lên.",

            "expected_answer":
                "CPA tối thiểu 2.00/4.00.",

            "answer_keywords": [
                "CPA",
                "2.00",
            ],
        },

        {
            "question":
                "Sinh viên cần hoàn thành "
                "GDQP-AN không?",

            "generated_answer":
                "Sinh viên phải hoàn thành "
                "Giáo dục Quốc phòng "
                "- An ninh.",

            "expected_answer":
                "Sinh viên phải hoàn thành "
                "GDQP-AN.",

            "answer_keywords": [
                "Giáo dục Quốc phòng",
                "An ninh",
            ],
        },

        {
            "question":
                "Sinh viên cần chuẩn "
                "ngoại ngữ nào?",

            "generated_answer":
                "Sinh viên cần đáp ứng "
                "chuẩn ngoại ngữ theo "
                "quy định của trường.",

            "expected_answer":
                "Sinh viên phải đạt "
                "TOEIC, IELTS hoặc "
                "VSTEP theo quy định.",

            "answer_keywords": [
                "TOEIC",
                "IELTS",
                "VSTEP",
            ],
        },
    ]

    batch_result = evaluator.evaluate_batch(
        test_items
    )

    print(
        "\n"
        "========================================"
    )

    print(
        "ANSWER EVALUATION SUMMARY"
    )

    print(
        "========================================"
    )

    summary = batch_result["summary"]

    print(
        f"Total Questions: "
        f"{summary['total_questions']}"
    )

    print(
        f"Correct: "
        f"{summary['correct']}"
    )

    print(
        f"Partially Correct: "
        f"{summary['partially_correct']}"
    )

    print(
        f"Incorrect: "
        f"{summary['incorrect']}"
    )

    print(
        f"Average Answer Score: "
        f"{summary['average_answer_score']}"
    )

    print(
        f"Average Answer Percentage: "
        f"{summary['average_answer_percentage']}%"
    )

    print(
        f"Correct Rate: "
        f"{summary['correct_rate_percentage']}%"
    )

    print(
        f"Partial Correct Rate: "
        f"{summary['partial_correct_rate_percentage']}%"
    )

    print(
        f"Incorrect Rate: "
        f"{summary['incorrect_rate_percentage']}%"
    )