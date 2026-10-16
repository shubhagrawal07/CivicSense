from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.authority import router as authority_router
from app.core.config import settings
from app.intelligence.text_classifier import load_text_model

settings.upload_path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app):
    load_text_model()
    yield


app = FastAPI(title="CivicSense", lifespan=lifespan)
# the token travels in a header, not a cookie, so credentials stay off
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(authority_router)
app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
