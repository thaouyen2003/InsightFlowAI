from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.data_service import DataService
from app.services.insight.insight_engine import (
    InsightEngine,
)
from app.services.insight.insight_models import (
    InsightCollection,
)

from app.services.knowledge.knowledge_builder import (
    KnowledgeBuilder,
)
from app.services.knowledge.knowledge_repository import (
    KnowledgeRepository,
)


router = APIRouter(
    prefix="/fusion",
    tags=["Insight Fusion"],
)


class FusionRequest(BaseModel):
    """
    Dữ liệu đầu vào của Fusion API.
    """

    filename: str


@router.post(
    "",
    response_model=InsightCollection,
)
def generate_fusion(
    request: FusionRequest,
) -> InsightCollection:
    """
    Phân tích dataset và trả về:

    - Insight
    - Recommendation
    - Summary
    """

    filename = request.filename.strip()

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename không được để trống.",
        )

    safe_filename = Path(filename).name

    try:
        data_service = DataService()

        df = data_service.load_dataframe(
            safe_filename
        )

        engine = InsightEngine()

        result = engine.generate(
            df=df,
            dataset_name=safe_filename,
        )

        insight_dicts = [
            insight.model_dump(
                mode="json",
            )
            for insight in result.insights
        ]

        recommendation_dicts = [
            recommendation.model_dump(
                mode="json",
            )
            for recommendation in result.recommendations
        ]

        knowledge_builder = KnowledgeBuilder()

        knowledge_collection = knowledge_builder.build(
            dataset_name=safe_filename,
            insights=insight_dicts,
            recommendations=recommendation_dicts,
        )

        knowledge_repository = KnowledgeRepository()

        knowledge_repository.save(
            knowledge_collection
        )

        return result

        return result

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Không tìm thấy dataset: "
                f"{safe_filename}"
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print(
            "Fusion generation failed:",
            str(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể tạo Insight Fusion "
                "và lưu kho tri thức."
            ),
        ) from error