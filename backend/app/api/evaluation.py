from fastapi import APIRouter
from pydantic import BaseModel

from app.services.data_service import data_service
from app.services.evaluation.dataset_classifier import (
    DatasetClassifier,
)

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


class EvaluationDetectRequest(BaseModel):
    filename: str


@router.post("/detect")
def detect_dataset(
    request: EvaluationDetectRequest,
):
    df = data_service.load_dataframe(
        request.filename
    )

    result = DatasetClassifier.classify(df)

    return {
        "success": True,
        "category": result.category,
        "label": result.label,
        "confidence": result.confidence,
        "matched_columns": result.matched_columns,
        "reasons": result.reasons,
    }