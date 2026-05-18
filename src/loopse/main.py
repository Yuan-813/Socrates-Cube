from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.loopse.api.health import router as health_router
from src.loopse.api.chat import router as chat_router

app = FastAPI(title="EduMultiAgent", version="0.1.0", description="Socrates-Cube")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
