from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dashboard import router as dashboard_router
from app.api.upload import router as upload_router
from app.api.schema import router as schema_router

from app.api.profile import router as profile_router

from app.api.dashboard import router as dashboard_router

from app.api.semantic import router as semantic_router

# Tạo FastAPI app trước
app = FastAPI(title="Insight Flow AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Router
app.include_router(upload_router)
app.include_router(dashboard_router)
app.include_router(schema_router)
app.include_router(profile_router)
app.include_router(dashboard_router)
app.include_router(semantic_router)