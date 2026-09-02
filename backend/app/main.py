"""
FastAPI 应用入口
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.utils.logger import logger
from app.utils.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("应用启动中...")
    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.warning(f"数据库初始化失败（可能MySQL未启动）: {e}")

    # 启动定时任务调度器
    try:
        from collector.scheduler import init_scheduler
        init_scheduler()
        logger.info("定时任务调度器已启动")
    except Exception as e:
        logger.warning(f"定时任务调度器启动失败: {e}")

    yield

    # 关闭时清理
    from collector.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("应用已关闭")


app = FastAPI(
    title="个股金融数据仓库与可视化大屏系统",
    description="支持A股个股数据采集、存储、可视化展示及AI智能问答",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api.stock import router as stock_router
from app.api.indicator import router as indicator_router
from app.api.dashboard import router as dashboard_router
from app.api.ai_chat import router as ai_chat_router

app.include_router(stock_router)
app.include_router(indicator_router)
app.include_router(dashboard_router)
app.include_router(ai_chat_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

# 挂载前端静态文件
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    from fastapi.responses import FileResponse
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )