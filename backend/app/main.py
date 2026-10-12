from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

settings.upload_path.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="CivicSense")
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
