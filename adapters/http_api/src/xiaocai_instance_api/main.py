"""
xiaocai HTTP API - 主入口

职责:
1. 创建 FastAPI 应用
2. 注册路由
3. 配置 CORS
4. 配置中间件

依赖: FLARE kernel (通过 kernel_client)
"""

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.settings import get_settings


def main():
    """主函数 - 启动 HTTP API 服务"""
    settings = get_settings()
    app = create_app()

    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
