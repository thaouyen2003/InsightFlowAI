from typing import Any
from uuid import uuid4

from app.services.knowledge.knowledge_models import (
    KnowledgeCollection,
    KnowledgeObject,
)


class KnowledgeBuilder:
    """
    Chuyển insight và recommendation thành
    các KnowledgeObject có thể lưu trữ.
    """

    def build(
        self,
        dataset_name: str,
        insights: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> KnowledgeCollection:
        items: list[KnowledgeObject] = []

        insight_knowledge = self._build_from_insights(
            dataset_name=dataset_name,
            insights=insights,
        )

        recommendation_knowledge = (
            self._build_from_recommendations(
                dataset_name=dataset_name,
                recommendations=recommendations,
            )
        )

        items.extend(insight_knowledge)
        items.extend(recommendation_knowledge)

        return KnowledgeCollection(
            dataset_name=dataset_name,
            total_knowledge=len(items),
            items=items,
        )

    def _build_from_insights(
        self,
        dataset_name: str,
        insights: list[dict[str, Any]],
    ) -> list[KnowledgeObject]:
        items: list[KnowledgeObject] = []

        for insight in insights:
            if not isinstance(insight, dict):
                continue

            title = str(
                insight.get(
                    "title",
                    "Insight chưa có tiêu đề",
                )
            )

            description = str(
                insight.get(
                    "description",
                    "",
                )
            )

            category = str(
                insight.get(
                    "category",
                    insight.get(
                        "type",
                        "insight",
                    ),
                )
            )

            evidence = insight.get(
                "evidence",
                {},
            )

            content = self._build_insight_content(
                title=title,
                description=description,
                evidence=evidence,
            )

            items.append(
                KnowledgeObject(
                    id=f"knowledge_{uuid4().hex}",
                    title=title,
                    content=content,
                    category=category,
                    source=dataset_name,
                    metadata={
                        "knowledge_type": "insight",
                        "insight_id": insight.get(
                            "id"
                        ),
                        "severity": insight.get(
                            "severity"
                        ),
                        "metric": insight.get(
                            "metric"
                        ),
                        "value": insight.get(
                            "value"
                        ),
                        "evidence": evidence,
                    },
                )
            )

        return items

    def _build_from_recommendations(
        self,
        dataset_name: str,
        recommendations: list[dict[str, Any]],
    ) -> list[KnowledgeObject]:
        items: list[KnowledgeObject] = []

        for recommendation in recommendations:
            if not isinstance(
                recommendation,
                dict,
            ):
                continue

            title = str(
                recommendation.get(
                    "title",
                    "Khuyến nghị",
                )
            )

            description = str(
                recommendation.get(
                    "description",
                    "",
                )
            )

            actions = recommendation.get(
                "actions",
                [],
            )

            content = (
                f"{title}. {description}"
            )

            if isinstance(actions, list) and actions:
                action_text = "; ".join(
                    str(action)
                    for action in actions
                )

                content = (
                    f"{content} "
                    f"Hành động đề xuất: {action_text}."
                )

            items.append(
                KnowledgeObject(
                    id=f"knowledge_{uuid4().hex}",
                    title=title,
                    content=content,
                    category="recommendation",
                    source=dataset_name,
                    metadata={
                        "knowledge_type": (
                            "recommendation"
                        ),
                        "recommendation_id": (
                            recommendation.get(
                                "id"
                            )
                        ),
                        "priority": (
                            recommendation.get(
                                "priority"
                            )
                        ),
                        "based_on": (
                            recommendation.get(
                                "based_on"
                            )
                        ),
                        "actions": actions,
                    },
                )
            )

        return items

    def _build_insight_content(
        self,
        title: str,
        description: str,
        evidence: Any,
    ) -> str:
        content = f"{title}. {description}"

        if isinstance(evidence, dict) and evidence:
            evidence_text = "; ".join(
                f"{key}: {value}"
                for key, value in evidence.items()
            )

            content = (
                f"{content} "
                f"Bằng chứng: {evidence_text}."
            )

        return content