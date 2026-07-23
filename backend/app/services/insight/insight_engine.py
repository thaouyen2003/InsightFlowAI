from typing import Any

import pandas as pd

from app.services.insight.detectors.duplicate_detector import (
    DuplicateDetector,
)
from app.services.insight.detectors.missing_detector import (
    MissingDetector,
)
from app.services.insight.insight_models import (
    InsightCollection,
    InsightObject,
)
from app.services.insight.insight_pipeline import (
    InsightPipeline,
)
from app.services.insight.detectors.numeric_detector import (
    NumericDetector,
)
from app.services.insight.detectors.category_detector import (
    CategoryDetector,
)
from app.services.insight.detectors.correlation_detector import (
    CorrelationDetector,
)
from app.services.insight.detectors.trend_detector import (
    TrendDetector,
)
from app.services.insight.recommendation_engine import (
    RecommendationEngine,
)

class InsightEngine:
    """
    Sinh Insight Objects từ DataFrame,
    DataContext và DatasetProfile.
    """

    def __init__(self) -> None:
        self.missing_detector = MissingDetector()
        self.duplicate_detector = DuplicateDetector()
        self.numeric_detector = NumericDetector()
        self.category_detector = CategoryDetector()
        self.correlation_detector = CorrelationDetector()
        self.trend_detector = TrendDetector()

        self.pipeline = InsightPipeline(
            max_insights=20,
        )

        self.recommendation_engine = (
            RecommendationEngine()
        )

        


    def generate(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None = None,
        dataset_profile: dict[str, Any] | None = None,
        dataset_name: str = "dataset",
    ) -> InsightCollection:

        insights: list[InsightObject] = []

        insights.extend(
            self._generate_missing_insights(df)
        )

        insights.extend(
            self._generate_duplicate_insights(df)
        )

        insights.extend(
            self._generate_numeric_insights(
                df=df,
                data_context=data_context,
            )
        )

        insights.extend(
            self._generate_category_insights(
                df=df,
                data_context=data_context,
            )
        )

        insights.extend(
            self._generate_time_insights(
                df=df,
                data_context=data_context,
            )
        )

        insights.extend(
            self.correlation_detector.detect(df)
        )

        insights.extend(
            self.trend_detector.detect(df)
        )

       

        # Knowledge Fusion Pipeline
        insights = self.pipeline.process(
            insights
        )
        recommendations = (
            self.recommendation_engine.generate(
                insights
            )
        )

        return InsightCollection(
            dataset_name=dataset_name,
            total_insights=len(insights),
            insights=insights,
            summary=self._build_summary(
                insights
            ),
            recommendations=recommendations,

        )



    def _generate_missing_insights(
        self,
        df: pd.DataFrame,
    ) -> list[InsightObject]:

        return self.missing_detector.detect(df)

    def _generate_duplicate_insights(
        self,
        df: pd.DataFrame,
    ) -> list[InsightObject]:

        return self.duplicate_detector.detect(df)

    def _generate_numeric_insights(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None,
    ) -> list[InsightObject]:

        return self.numeric_detector.detect(
            df=df,
            data_context=data_context,
        )

    def _generate_category_insights(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None,
    ) -> list[InsightObject]:

        return self.category_detector.detect(
            df=df,
            data_context=data_context,
        )

    def _generate_time_insights(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None,
    ) -> list[InsightObject]:

        return []

    def _build_summary(
        self,
        insights: list[InsightObject],
    ) -> dict[str, int]:

        summary: dict[str, int] = {}

        for insight in insights:
            key = insight.type.value
            summary[key] = summary.get(key, 0) + 1

        return summary