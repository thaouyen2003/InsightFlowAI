"""
profile.py

Dataset Profile API

Author: InsightFlow AI
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.profiler import DataProfiler

router = APIRouter(
    prefix="/profile",
    tags=["Data Profiler"],
)

profiler = DataProfiler()


@router.post("/")
async def profile_dataset(
    file: UploadFile = File(...),
):
    """
    Generate dataset profile.
    """

    try:

        filename = file.filename.lower()

        content = await file.read()

        # --------------------------------------------------
        # Read CSV
        # --------------------------------------------------

        if filename.endswith(".csv"):

            df = pd.read_csv(
                BytesIO(content)
            )

        # --------------------------------------------------
        # Read Excel
        # --------------------------------------------------

        elif filename.endswith((".xlsx", ".xls")):

            df = pd.read_excel(
                BytesIO(content)
            )

        else:

            raise HTTPException(
                status_code=400,
                detail="Unsupported file format.",
            )

        # --------------------------------------------------

        result = profiler.profile(df)

        return {
            "success": True,
            "filename": file.filename,
            "profile": result,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )