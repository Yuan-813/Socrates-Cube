from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="EduMultiAgent",
    version="0.1.0",
    description="Socrates-Cube 多智能体自适应学习系统",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/chat/test", tags=["对话"])
async def chat_test():
    return {"message": "后端联通成功"}
