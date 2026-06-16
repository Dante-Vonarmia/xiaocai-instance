"""
配置管理

职责:
1. 加载环境变量
2. 提供配置访问接口
3. 校验配置完整性

环境变量:
- API_HOST: API 监听地址（默认 0.0.0.0）
- API_PORT: API 监听端口（默认 8001）
- INSTANCE_JWT_SECRET: JWT 签名密钥
- KERNEL_HOST: FLARE kernel 地址
- KERNEL_PORT: FLARE kernel 端口
- FLARE_DOMAIN_PACK_ROOT: 资产根目录（domain-packs）
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API 配置
    api_host: str = Field(default="0.0.0.0", description="API 监听地址")
    api_port: int = Field(default=8001, description="API 监听端口")
    gzip_minimum_size: int = Field(default=1024, description="启用 gzip 的最小响应字节数")
    message_window_initial_limit: int = Field(default=6, description="会话初始消息窗口条数")

    # CORS 配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="允许的 CORS 源"
    )

    # JWT 配置
    instance_jwt_secret: str = Field(
        default="change-me-in-development-secret-32+",
        description="JWT 签名密钥",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    jwt_expire_minutes: int = Field(default=60*24*7, description="JWT 过期时间（分钟）")

    # FLARE Kernel 配置
    kernel_runtime_mode: str = Field(default="http", description="Kernel 调用模式: http")
    kernel_base_url_override: str = Field(
        default="",
        alias="KERNEL_BASE_URL",
        description="FLARE kernel 完整地址（可选，优先级高于 host/port）",
    )
    kernel_host: str = Field(default="localhost", description="FLARE kernel 地址")
    kernel_port: int = Field(default=8000, description="FLARE kernel 端口")
    kernel_run_path: str = Field(default="/kernel/run", description="Kernel 同步对话路径")
    kernel_action_path: str = Field(default="/kernel/action", description="Kernel 动作路径")
    kernel_stream_path: str = Field(default="/kernel/stream", description="Kernel 流式对话路径")

    # Domain Pack 配置（domain-packs）
    flare_instance_id: str = Field(default="xiaocai", description="FLARE instance 标识")
    flare_domain_pack_default_domain: str = Field(default="xiaocai", description="默认领域包 domain")
    flare_domain_pack_version: str = Field(default="default", description="默认领域包版本")
    flare_domain_pack_root: str = Field(default=".", description="领域资产根目录（domain-packs）")
    upload_root: str = Field(default="/tmp/xiaocai-instance-uploads", description="上传文件存储根目录")
    storage_db_path: str = Field(default="/tmp/xiaocai-instance.db", description="SQLite 存储路径")
    storage_db_url: str = Field(default="", description="数据库连接串（优先，支持 postgresql://）")
    upload_max_size_bytes: int = Field(default=20 * 1024 * 1024, description="上传文件最大字节数")
    upload_allowed_extensions: List[str] = Field(
        default=[
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "csv",
            "txt",
            "md",
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        description="允许上传的文件扩展名",
    )
    enabled_modes: List[str] = Field(
        default=["auto", "requirement_canvas", "analysis_mode", "intelligent_sourcing"],
        description="允许的业务模式",
    )
    daily_message_limit: int = Field(default=0, description="每日消息上限，0 表示不限制")
    daily_project_message_limit: int = Field(default=0, description="每日单项目消息上限，0 表示不限制")
    chat_replay_enabled: bool = Field(default=False, description="是否记录 chat kernel replay 调试日志")
    chat_replay_dir: str = Field(default="/tmp/xiaocai-chat-replays", description="chat replay 调试日志目录")

    # 外部连接健康检查
    mcp_healthcheck_url: str = Field(default="", description="MCP 连接健康检查 URL（可选）")
    external_search_healthcheck_url: str = Field(default="", description="外部搜索连接健康检查 URL（可选）")

    # 认证配置
    mock_auth: bool = Field(default=True, description="是否使用 Mock 认证")
    real_auth_verify_url: str = Field(default="", description="真实认证验证 URL")
    caigou_china_auth_verify_url: str = Field(default="", description="采购中国登录凭证校验 URL")
    caigou_china_app_id: str = Field(default="yunhe_ai", description="采购中国分配的应用 ID")
    caigou_china_app_secret: str = Field(default="", description="采购中国接口签名密钥")
    public_test_auth_enabled: bool = Field(default=False, description="是否启用公开测试 credential")
    public_test_credential: str = Field(default="", description="公开测试 credential")
    public_test_user_id: str = Field(default="public-test-user", description="公开测试账号用户 ID")
    public_test_display_name: str = Field(default="公开测试用户", description="公开测试账号展示名")
    root_auth_token: str = Field(default="", description="root 认证 token")
    root_user_id: str = Field(default="root", description="root 用户 ID")

    @property
    def kernel_base_url(self) -> str:
        """FLARE kernel 基础 URL"""
        if self.kernel_base_url_override and self.kernel_base_url_override.strip():
            return self.kernel_base_url_override.strip().rstrip("/")
        return f"http://{self.kernel_host}:{self.kernel_port}"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
