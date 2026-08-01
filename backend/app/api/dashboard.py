import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.dashboard.dashboard_service import (
    DashboardService,
)
from app.services.data_service import data_service


router = APIRouter()

service = DashboardService()


class DashboardRequest(BaseModel):
    filename: str


@router.post("/dashboard")
def generate_dashboard(
    request: DashboardRequest,
):
    try:
        print(
            "\n===== DASHBOARD REQUEST ====="
        )
        print(
            "Filename:",
            request.filename,
        )

        # 1. Đọc DataFrame
        df = data_service.load_dataframe(
            request.filename
        )

        print(
            "Loaded dataframe:",
            {
                "rows": len(df),
                "columns": len(df.columns),
            },
        )

        # 2. Tạo dashboard
        dashboard_result = service.generate(df)

        print(
            "Generated dashboard:",
            {
                "status": dashboard_result.get(
                    "status"
                ),
                "kpi_count": len(
                    dashboard_result.get(
                        "kpis",
                        [],
                    )
                ),
                "chart_count": len(
                    dashboard_result.get(
                        "charts",
                        [],
                    )
                ),
                "warning_count": len(
                    dashboard_result.get(
                        "warnings",
                        [],
                    )
                ),
            },
        )

        print(
            "=============================\n"
        )

        return dashboard_result

    except FileNotFoundError as error:
        print(
            "\n===== FILE NOT FOUND ====="
        )
        traceback.print_exc()
        print(
            "==========================\n"
        )

        raise HTTPException(
            status_code=404,
            detail=(
                f"Không tìm thấy file: "
                f"{request.filename}"
            ),
        ) from error

    except ValueError as error:
        print(
            "\n===== INVALID DATA ====="
        )
        traceback.print_exc()
        print(
            "========================\n"
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except HTTPException:
        # Giữ nguyên HTTPException từ service
        raise

    except Exception as error:
        print(
            "\n===== DASHBOARD API ERROR ====="
        )
        traceback.print_exc()
        print(
            "===============================\n"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể tạo dashboard: "
                f"{str(error)}"
            ),
        ) from error