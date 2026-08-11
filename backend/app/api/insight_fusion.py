from fastapi import APIRouter, HTTPException

from app.services.data_service import DataService
from app.services.fusion.fusion_models import (
    FusionRequest,
    FusionResponse,
)
from app.services.fusion.insight_fusion_service import (
    InsightFusionService,
)
from app.services.insight.insight_engine import (
    InsightEngine,
)
from app.services.rag.rag_service import (
    RAGService,
)


router = APIRouter(
    prefix="/insight-fusion",
    tags=["Insight Fusion"],
)


data_service = DataService()
insight_engine = InsightEngine()
rag_service = RAGService()

fusion_service = InsightFusionService(
    insight_engine=insight_engine,
    knowledge_service=rag_service,
)


@router.post(
    "",
    response_model=FusionResponse,
)
def generate_insight_fusion(
    request: FusionRequest,
) -> FusionResponse:
    try:
        df = data_service.load_dataframe(
            request.filename
        )

        return fusion_service.generate(
            df=df,
            dataset_name=request.filename,
            category=request.category,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể tạo Insight Fusion: "
                f"{exc}"
            ),
        ) from exc