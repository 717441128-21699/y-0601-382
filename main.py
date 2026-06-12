from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base, SessionLocal
from models import *
from game_data import init_game_data
from routers import (
    account_router,
    inventory_router,
    quest_router,
    dialogue_router,
    battle_router,
    savegame_router,
    leaderboard_router,
    achievement_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        init_game_data(db)
    finally:
        db.close()
    
    yield


app = FastAPI(
    title="角色扮演游戏后端服务",
    description="文字冒险平台玩家角色和剧情进度管理系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account_router)
app.include_router(inventory_router)
app.include_router(quest_router)
app.include_router(dialogue_router)
app.include_router(battle_router)
app.include_router(savegame_router)
app.include_router(leaderboard_router)
app.include_router(achievement_router)


@app.get("/")
def root():
    return {
        "name": "角色扮演游戏后端服务",
        "version": "1.0.0",
        "description": "文字冒险平台玩家角色和剧情进度管理系统",
        "api_docs": "/docs",
        "modules": [
            "账号角色 - /api/account",
            "属性成长 - /api/account (add_exp, add_gold)",
            "背包装备 - /api/inventory",
            "任务状态 - /api/quest",
            "对话选择 - /api/dialogue",
            "战斗结算 - /api/battle",
            "存档读取 - /api/savegame",
            "排行榜 - /api/leaderboard",
            "成就系统 - /api/achievement"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2026-06-13"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
