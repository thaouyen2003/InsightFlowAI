from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel

from app.services.data_service import DATA_DIR
from app.services.scholarship.models import (
    ScholarshipEvaluationResponse,
)
from app.services.scholarship.service import (
    ScholarshipEvaluationService,
)


router = APIRouter(
    prefix="/scholarship",
    tags=["Scholarship Evaluation"],
)


class StoredScholarshipEvaluationRequest(
    BaseModel
):
    """
    Request đánh giá dataset đã được endpoint
    /upload lưu trên hệ thống.
    """

    filename: str

    rule_set_code: str = "scholarship_test"


def read_uploaded_dataframe(
    *,
    filename: str,
    content: bytes,
) -> pd.DataFrame:
    """
    Chuyển nội dung CSV, Excel hoặc JSON
    được upload thành pandas DataFrame.
    """

    normalized_filename = (
        filename.lower().strip()
    )

    if normalized_filename.endswith(".csv"):
        try:
            return pd.read_csv(
                BytesIO(content),
                encoding="utf-8-sig",
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                BytesIO(content),
                encoding="latin-1",
            )

    if normalized_filename.endswith(
        (".xlsx", ".xls")
    ):
        return pd.read_excel(
            BytesIO(content)
        )

    if normalized_filename.endswith(".json"):
        return pd.read_json(
            BytesIO(content)
        )

    raise ValueError(
        "Định dạng file không được hỗ trợ. "
        "Chỉ chấp nhận CSV, XLSX, XLS hoặc JSON."
    )


@router.post(
    "/evaluate",
    response_model=ScholarshipEvaluationResponse,
)
async def evaluate_scholarship(
    file: UploadFile = File(...),
    rule_set_code: str = Form(
        default="scholarship_test"
    ),
) -> ScholarshipEvaluationResponse:
    """
    Nhận trực tiếp file dữ liệu sinh viên và
    đánh giá điều kiện học bổng.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File upload không có tên.",
        )

    try:
        content = await file.read()

        if not content:
            raise ValueError(
                "File upload không có dữ liệu."
            )

        df = read_uploaded_dataframe(
            filename=file.filename,
            content=content,
        )

        service = ScholarshipEvaluationService()

        return service.evaluate(
            df=df,
            dataset_name=file.filename,
            rule_set_code=rule_set_code,
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        ValueError,
        TypeError,
        pd.errors.ParserError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể đánh giá điều kiện "
                f"học bổng: {error}"
            ),
        ) from error

    finally:
        await file.close()


@router.post(
    "/evaluate-stored",
    response_model=ScholarshipEvaluationResponse,
)
def evaluate_stored_scholarship(
    request: StoredScholarshipEvaluationRequest,
) -> ScholarshipEvaluationResponse:
    """
    Đánh giá dataset đã được endpoint /upload
    lưu trong DATA_DIR.

    Frontend không cần upload file lần thứ hai.
    """

    safe_filename = Path(
        request.filename
    ).name

    if not safe_filename:
        raise HTTPException(
            status_code=400,
            detail="Tên file không hợp lệ.",
        )

    file_path = DATA_DIR / safe_filename

    try:
        service = ScholarshipEvaluationService()

        return service.evaluate_file(
            file_path=file_path,
            rule_set_code=request.rule_set_code,
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        ValueError,
        TypeError,
        pd.errors.ParserError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể đánh giá file học bổng "
                f"đã lưu: {error}"
            ),
        ) from error