from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.dashboard.dashboard_service import DashboardService
from app.services.data_service import data_service


router = APIRouter()

service = DashboardService()


class DashboardRequest(BaseModel):
    filename: str


@router.post("/dashboard")
def generate_dashboard(request: DashboardRequest):
    try:
        # Đọc DataFrame thông qua DataService
        df = data_service.load_dataframe(request.filename)

        # Tạo dashboard
        dashboard_result = service.generate(df)

        print("\n========== DASHBOARD RESULT ==========")

        print("Status:", dashboard_result["status"])

        print("KPI:", len(dashboard_result["kpis"]))

        print("Charts:", len(dashboard_result["charts"]))

        print("\nWarnings:")

        for warning in dashboard_result["warnings"]:
            print("-", warning)

        print("=====================================\n")

        # print(
        #     "Generated dashboard:",
        #     {
        #         "status": dashboard_result.get("status"),
        #         "kpi_count": len(
        #             dashboard_result.get("kpis", [])
        #         ),
        #         "chart_count": len(
        #             dashboard_result.get("charts", [])
        #         ),
        #         "warning_count": len(
        #             dashboard_result.get("warnings", [])
        #         ),
        #     },
        # )

        return dashboard_result

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy file: {request.filename}",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print("Dashboard API error:", str(error))

        raise HTTPException(
            status_code=500,
            detail=f"Không thể tạo dashboard: {str(error)}",
        )