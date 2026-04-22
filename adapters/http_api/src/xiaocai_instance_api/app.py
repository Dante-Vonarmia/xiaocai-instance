"""
FastAPI 应用工厂

职责:
1. 创建 FastAPI 实例
2. 注册所有路由
3. 配置 CORS
4. 配置全局异常处理
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.auth.router import router as auth_router
from xiaocai_instance_api.chat.router import router as chat_router
from xiaocai_instance_api.projects.router import router as projects_router
from xiaocai_instance_api.sessions.router import router as sessions_router, chat_compat_router
from xiaocai_instance_api.sources.router import (
    router as sources_router,
    project_compat_router as sources_project_compat_router,
    chat_project_compat_router as sources_chat_project_compat_router,
    files_compat_router as sources_files_compat_router,
    chat_files_compat_router as sources_chat_files_compat_router,
)
from xiaocai_instance_api.conversations.router import router as conversations_router
from xiaocai_instance_api.artifacts.router import router as artifacts_router
from xiaocai_instance_api.retrieval.router import router as retrieval_router
from xiaocai_instance_api.tenant_profile.router import router as tenant_profile_router
from xiaocai_instance_api.recommendation_policy.router import router as recommendation_policy_router
from xiaocai_instance_api.integrations.router import router as integrations_router
from xiaocai_instance_api.domains.router import router as domains_router
from xiaocai_instance_api.storage.migrations import run_storage_migrations


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    Returns:
        FastAPI: 配置好的应用实例
    """
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        run_storage_migrations(
            db_path=settings.storage_db_path,
            db_url=settings.storage_db_url,
        )
        yield

    app = FastAPI(
        title="xiaocai Instance API",
        description="xiaocai 采购助手 HTTP API（基于 FLARE kernel）",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(projects_router)
    app.include_router(sessions_router)
    app.include_router(chat_compat_router)
    app.include_router(sources_router)
    app.include_router(sources_project_compat_router)
    app.include_router(sources_chat_project_compat_router)
    app.include_router(sources_files_compat_router)
    app.include_router(sources_chat_files_compat_router)
    app.include_router(conversations_router)
    app.include_router(artifacts_router)
    app.include_router(retrieval_router)
    app.include_router(tenant_profile_router)
    app.include_router(recommendation_policy_router)
    app.include_router(integrations_router)
    app.include_router(domains_router)

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "ok", "service": "xiaocai-api"}

    return app
