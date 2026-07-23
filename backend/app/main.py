from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.knowledge.knowledge_router import (
    router as knowledge_router,
)
from app.api.insight_fusion import (
    router as insight_fusion_router,
)


from app.api.upload import (
    router as upload_router,
)

from app.api.dashboard import (
    router as dashboard_router,
)

from app.api.schema import (
    router as schema_router,
)

from app.api.profile import (
    router as profile_router,
)

# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="InsightFlowAI API",
    description=(
        "Backend API cho hệ thống InsightFlowAI: "
        "phân tích dữ liệu, sinh insight và truy xuất "
        "tri thức giáo dục bằng RAG."
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# Cho phép frontend Next.js gọi API từ localhost:3000
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTERS
# =========================================================
app.include_router(upload_router)
app.include_router(schema_router)
app.include_router(profile_router)
app.include_router(dashboard_router)
app.include_router(knowledge_router)
app.include_router(insight_fusion_router)

# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get(
    "/",
    tags=["System"],
)
def root() -> dict[str, str]:
    """
    Kiểm tra trạng thái hoạt động của backend.
    """

    return {
        "status": "success",
        "message": "InsightFlowAI API is running",
        "docs": "/docs",
        "knowledge_health": "/knowledge/health",
        "knowledge_ask": "/knowledge/ask",
    }


# =========================================================
# APPLICATION HEALTH CHECK
# =========================================================

@app.get(
    "/health",
    tags=["System"],
)
def health_check() -> dict[str, str]:
    """
    Health check tổng quát của hệ thống.
    """

    return {
        "status": "healthy",
        "service": "InsightFlowAI Backend",
    }