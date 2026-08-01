from fastapi import APIRouter, UploadFile, File
import pandas as pd

router = APIRouter()

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(file.file)

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(file.file)

    elif filename.endswith(".json"):
        df = pd.read_json(file.file)

    else:
        return {
            "success": False,
            "message": "Unsupported file format"
        }

    return {
        "success": True,
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict(orient="records")
    }