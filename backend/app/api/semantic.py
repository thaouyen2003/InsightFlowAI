import io
import pandas as pd

from app.services.semantic_analysis.column_analyzer import ColumnAnalyzer


from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)


router = APIRouter(
    prefix="/semantic",
    tags=["Semantic Analyzer"],
)


@router.post("/analyze")
async def analyze_columns(
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        filename = file.filename or ""

        if filename.lower().endswith(".csv"):
            df = pd.read_csv(
                io.BytesIO(content)
            )

        elif filename.lower().endswith(
            (".xlsx", ".xls")
        ):
            df = pd.read_excel(
                io.BytesIO(content)
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Hiện tại chỉ hỗ trợ "
                    "file CSV và Excel."
                ),
            )

        analyzer = ColumnAnalyzer()

        columns = analyzer.analyze(df)

        role_summary = {
            "identifiers": sum(
                1
                for column in columns
                if column["role"] == "identifier"
            ),
            "dimensions": sum(
                1
                for column in columns
                if column["role"] == "dimension"
            ),
            "measures": sum(
                1
                for column in columns
                if column["role"] == "measure"
            ),
            "unsupported": sum(
                1
                for column in columns
                if column["role"] == "unsupported"
            ),
        }

        return {
            "success": True,
            "filename": filename,
            "rows": len(df),
            "column_count": len(df.columns),
            "role_summary": role_summary,
            "columns": columns,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể phân tích dữ liệu: "
                f"{str(error)}"
            ),
        )