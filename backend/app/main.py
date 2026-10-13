from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.intelligence.text_classifier import load_text_model

settings.upload_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app):
    load_text_model()
    yield


app = FastAPI(title="CivicSense", lifespan=lifespan)
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
