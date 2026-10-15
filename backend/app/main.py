from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.authority import router as authority_router
from app.core.config import settings

settings.upload_path.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="CivicSense")
app.include_router(auth_router)
app.include_router(authority_router)
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
