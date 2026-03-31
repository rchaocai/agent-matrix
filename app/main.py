"""
Agent Matrix - AI驱动的内容矩阵管理系统

主应用入口文件
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from app.config import settings
from app.core.scheduler import SchedulerService
from app.core.agent_manager import AgentManager
from app.core.llm_service import create_llm_service_from_env


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# 全局服务
scheduler_service: SchedulerService = None
agent_manager: AgentManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global scheduler_service, agent_manager

    # 启动时初始化
    logger.info("正在启动Agent Matrix...")

    # 创建数据目录
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.content_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.drafts_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)

    # 初始化 Tortoise ORM
    from tortoise import Tortoise
    await Tortoise.init(
        db_url=settings.database_url,
        modules={'models': ['app.models.agent', 'app.models.content',
                           'app.models.task', 'app.models.draft',
                           'app.models.account', 'app.models.review',
                           'app.models.user', 'app.models.session',
                           'app.models.audit_log', 'app.models.prompt_template',
                           'app.models.review_settings']}
    )
    await Tortoise.generate_schemas()
    logger.info("数据库初始化完成")

    # 初始化服务
    agent_manager = AgentManager()

    # 初始化 LLM 服务
    llm_service = create_llm_service_from_env()
    agent_manager.set_llm_service(llm_service)
    logger.info(f"LLM 服务初始化完成，默认提供商: {llm_service.default_provider}")

    # 初始化 Skill Registry
    from app.skills.skill_loader import SkillRegistry
    skill_registry = SkillRegistry(settings.skills_dir)
    await skill_registry.initialize()
    agent_manager.set_skills_registry(skill_registry)
    logger.info("Skill 加载完成")

    # 先创建并启动调度器
    scheduler_service = SchedulerService(agent_manager)
    await scheduler_service.start()

    # 再加载Agent（此时可以调度）
    await agent_manager.load_agents_from_config()

    logger.info("Agent Matrix启动完成")

    yield

    # 关闭时清理
    logger.info("正在关闭Agent Matrix...")
    if scheduler_service:
        await scheduler_service.stop()

    await Tortoise.close_connections()
    logger.info("Agent Matrix已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Agent Matrix",
    description="AI驱动的内容矩阵管理系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
from fastapi.middleware.cors import CORSMiddleware
import os

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源（开发环境）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
    max_age=600,  # 预检请求缓存时间
    expose_headers=["*"],
)

# 静态文件服务
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 确保data目录存在
Path("data").mkdir(exist_ok=True)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="data"), name="static")

# 导入路由
from app.api.routes import agents, content, drafts, reviews, dashboard, accounts, statistics, render, publish
from app.api.routes import tasks as tasks_routes
from app.api.routes import settings as settings_router
from app.api.routes import auth
from app.api.routes import prompt_templates
from app.api.routes import review_settings
from app.api.routes import hot_search

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agent管理"])
app.include_router(content.router, prefix="/api/content", tags=["内容管理"])
app.include_router(tasks_routes.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["草稿管理"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["审核管理"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘统计"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["账号管理"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["数据统计"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["系统设置"])
app.include_router(render.router, prefix="/api/render", tags=["渲染服务"])
app.include_router(publish.router, prefix="/api/publish", tags=["发布服务"])
app.include_router(prompt_templates.router, prefix="/api/prompt-templates", tags=["提示词模板"])
app.include_router(review_settings.router, prefix="/api/review-settings", tags=["审核设置"])
app.include_router(hot_search.router, prefix="/api/hot-search", tags=["热搜管理"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Agent Matrix API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "scheduler": scheduler_service is not None and scheduler_service.running,
            "agent_manager": agent_manager is not None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
