from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import logging

from app.core.config import settings
from app.api.chat import router as chat_router


app = FastAPI(
    title="SkinMatch Chatbot Backend",
    description="Session memory + OpenAI chat over analysis context",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
)


origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

app.include_router(chat_router, prefix="/api/v1", tags=["chatbot"])


@app.get("/")
def root():
    return {"service": "chatbot", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "chatbot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
