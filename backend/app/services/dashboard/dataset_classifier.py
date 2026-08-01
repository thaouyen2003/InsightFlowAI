from typing import Any


class DatasetClassifier:
    """
    Phân loại dataset dựa trên semantic metadata.

    Dataset hỗ trợ:
    - sales
    - finance
    - inventory
    - customer
    - marketing
    - human_resources
    - operations
    - survey
    - generic
    """

    DATASET_RULES = {
        "sales": {
            "keywords": {
                "order",
                "orders",
                "sale",
                "sales",
                "revenue",
                "price",
                "quantity",
                "customer",
                "product",
                "profit",
                "discount",
                "payment",
                "invoice",
            },
            "minimum_score": 3,
        },
        "finance": {
            "keywords": {
                "revenue",
                "expense",
                "income",
                "cost",
                "profit",
                "budget",
                "cash",
                "asset",
                "liability",
                "equity",
                "balance",
                "account",
                "transaction",
            },
            "minimum_score": 3,
        },
        "inventory": {
            "keywords": {
                "inventory",
                "stock",
                "warehouse",
                "quantity",
                "product",
                "supplier",
                "reorder",
                "sku",
                "item",
                "received",
                "delivery",
            },
            "minimum_score": 3,
        },
        "customer": {
            "keywords": {
                "customer",
                "client",
                "city",
                "state",
                "region",
                "segment",
                "gender",
                "age",
                "email",
                "phone",
                "address",
            },
            "minimum_score": 3,
        },
        "marketing": {
            "keywords": {
                "campaign",
                "channel",
                "click",
                "impression",
                "conversion",
                "lead",
                "traffic",
                "engagement",
                "reach",
                "advertising",
                "marketing",
            },
            "minimum_score": 3,
        },
        "human_resources": {
            "keywords": {
                "employee",
                "staff",
                "salary",
                "department",
                "position",
                "hire",
                "attendance",
                "performance",
                "manager",
                "job",
                "workforce",
            },
            "minimum_score": 3,
        },
        "operations": {
            "keywords": {
                "process",
                "operation",
                "duration",
                "status",
                "machine",
                "production",
                "quality",
                "downtime",
                "maintenance",
                "capacity",
                "output",
            },
            "minimum_score": 3,
        },
        "survey": {
            "keywords": {
                "survey",
                "question",
                "answer",
                "response",
                "rating",
                "score",
                "satisfaction",
                "feedback",
                "respondent",
            },
            "minimum_score": 3,
        },
    }

    def classify(
        self,
        data_context: dict[str, Any],
    ) -> dict[str, Any]:
        columns = data_context.get("columns", [])

        normalized_names = {
            column.get("normalized_name", "")
            for column in columns
        }

        semantic_types = {
            column.get("semantic_type", "")
            for column in columns
        }

        scores = self._calculate_scores(
            normalized_names=normalized_names,
            semantic_types=semantic_types,
        )

        dataset_type, score = self._select_best_type(
            scores
        )

        confidence = self._calculate_confidence(
            score=score,
            total_columns=len(columns),
        )

        matched_signals = self._get_matched_signals(
            dataset_type=dataset_type,
            normalized_names=normalized_names,
        )

        return {
            "dataset_type": dataset_type,
            "confidence": confidence,
            "score": score,
            "matched_signals": matched_signals,
            "scores": scores,
        }

    def _calculate_scores(
        self,
        normalized_names: set[str],
        semantic_types: set[str],
    ) -> dict[str, int]:
        scores: dict[str, int] = {}

        for dataset_type, rule in self.DATASET_RULES.items():
            score = 0
            keywords = rule["keywords"]

            for column_name in normalized_names:
                tokens = set(
                    column_name.split("_")
                )

                score += len(
                    tokens.intersection(keywords)
                )

            score += self._semantic_bonus(
                dataset_type=dataset_type,
                semantic_types=semantic_types,
            )

            scores[dataset_type] = score

        return scores

    def _semantic_bonus(
        self,
        dataset_type: str,
        semantic_types: set[str],
    ) -> int:
        bonus = 0

        if dataset_type in {
            "sales",
            "finance",
        }:
            if "currency" in semantic_types:
                bonus += 2

        if dataset_type == "inventory":
            if "quantity" in semantic_types:
                bonus += 2

        if dataset_type == "marketing":
            if "percentage" in semantic_types:
                bonus += 1

        if dataset_type == "survey":
            if "category" in semantic_types:
                bonus += 1

        return bonus

    def _select_best_type(
        self,
        scores: dict[str, int],
    ) -> tuple[str, int]:
        if not scores:
            return "generic", 0

        dataset_type = max(
            scores,
            key=scores.get,
        )

        score = scores[dataset_type]

        minimum_score = self.DATASET_RULES[
            dataset_type
        ]["minimum_score"]

        if score < minimum_score:
            return "generic", score

        return dataset_type, score

    def _calculate_confidence(
        self,
        score: int,
        total_columns: int,
    ) -> float:
        if total_columns == 0:
            return 0.0

        confidence = score / max(
            total_columns,
            1,
        )

        return round(
            min(confidence, 1.0),
            2,
        )

    def _get_matched_signals(
        self,
        dataset_type: str,
        normalized_names: set[str],
    ) -> list[str]:
        if dataset_type == "generic":
            return []

        keywords = self.DATASET_RULES[
            dataset_type
        ]["keywords"]

        matched_signals: list[str] = []

        for column_name in sorted(
            normalized_names
        ):
            tokens = set(
                column_name.split("_")
            )

            if tokens.intersection(keywords):
                matched_signals.append(
                    column_name
                )

        return matched_signals