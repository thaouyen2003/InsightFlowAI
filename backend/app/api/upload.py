from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.services.data_service import DATA_DIR


router = APIRouter()


def read_dataframe(
    *,
    filename: str,
    content: bytes,
) -> pd.DataFrame:
    """
    Đọc CSV, Excel hoặc JSON từ nội dung file.
    """

    extension = Path(filename).suffix.lower()

    if extension == ".csv":
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

    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(
            BytesIO(content)
        )

    if extension == ".json":
        return pd.read_json(
            BytesIO(content)
        )

    raise ValueError(
        "Định dạng file không được hỗ trợ. "
        "Chỉ chấp nhận CSV, XLSX, XLS hoặc JSON."
    )


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
):
    """
    Upload dataset, lưu file vào database_input
    và trả thông tin tổng quan cho frontend.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File upload không có tên.",
        )

    # Chỉ lấy tên file, loại bỏ đường dẫn nguy hiểm.
    safe_filename = Path(file.filename).name

    try:
        content = await file.read()

        if not content:
            raise ValueError(
                "File upload không có dữ liệu."
            )

        # Đọc thử trước để chắc chắn file hợp lệ.
        df = read_dataframe(
            filename=safe_filename,
            content=content,
        )

        # Đảm bảo thư mục lưu trữ tồn tại.
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Đây cũng là nơi DashboardService đang đọc file.
        stored_path = DATA_DIR / safe_filename
        stored_path.write_bytes(content)

        return {
            "success": True,
            "filename": safe_filename,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(
                orient="records"
            ),
        }

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
                "Không thể tải và lưu dataset: "
                f"{error}"
            ),
        ) from error

    finally:
        await file.close()
