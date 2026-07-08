"""
Schema API

Nhiệm vụ:
- Nhận file từ Frontend
- Chuyển thành DataFrame
- Gọi Schema Analyzer
- Trả kết quả về Frontend
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
import pandas as pd

from app.services.schema.analyzer import SchemaAnalyzer

router = APIRouter(
    prefix="/schema",
    tags=["Schema Analyzer"]
)


@router.post("/analyze")
async def analyze_schema(
    file: UploadFile = File(...)
):
    """
    Phân tích schema của file người dùng upload.
    """

    try:

        filename = file.filename.lower()

        # ==========================
        # Đọc CSV
        # ==========================

        if filename.endswith(".csv"):

            df = pd.read_csv(file.file)

        # ==========================
        # Đọc Excel
        # ==========================

        elif filename.endswith(".xlsx"):

            df = pd.read_excel(file.file)

        else:

            raise HTTPException(
                status_code=400,
                detail="Chỉ hỗ trợ CSV và Excel."
            )

        # ==========================
        # Phân tích Schema
        # ==========================

        analyzer = SchemaAnalyzer()

        result = analyzer.analyze(df)

        # ==========================
        # Trả kết quả
        # ==========================

        return {
            "success": True,
            "filename": file.filename,
            "analysis": result.to_dict()
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )