from fastapi import APIRouter
from pydantic import BaseModel

from app.services.dashboard.dashboard_service import DashboardService
from app.services.data_service import data_service

router = APIRouter()

service = DashboardService()


class DashboardRequest(BaseModel):
    filename: str


@router.post("/dashboard")
def generate_dashboard(request: DashboardRequest):

    # Đọc DataFrame thông qua DataService
    df = data_service.load_dataframe(request.filename)

    # Tạo dashboard
    dashboard = service.generate(df)

    return dashboard