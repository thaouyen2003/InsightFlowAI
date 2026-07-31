from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.services.graduation.models import (
    GraduationEvaluationResponse,
)
from app.services.graduation.service import (
    GraduationEvaluationService,
)


router = APIRouter(
    prefix="/graduation",
    tags=["Graduation Evaluation"],
)


def read_uploaded_dataframe(
    *,
    filename: str,
    content: bytes,
) -> pd.DataFrame:
    """
    Chuyển file CSV, Excel hoặc JSON được upload
    thành pandas DataFrame.
    """

    normalized_filename = filename.lower().strip()

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
    response_model=GraduationEvaluationResponse,
)
async def evaluate_graduation(
    file: UploadFile = File(...),
    rule_set_code: str = Form(
        default="qd_xtn_dh_chinh_quy_vhu"
    ),
) -> GraduationEvaluationResponse:
    """
    Nhận file dữ liệu sinh viên và đánh giá
    điều kiện tốt nghiệp bằng bộ luật được sinh
    từ kho tri thức.
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

        service = GraduationEvaluationService()

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
                f"tốt nghiệp: {error}"
            ),
        ) from error

    finally:
        await file.close()
