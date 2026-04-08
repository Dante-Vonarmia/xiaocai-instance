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
- FLARE_DOMAIN_PACK_ROOT: domain-pack 根目录
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
    kernel_run_path: str = Field(default="/chat/run", description="Kernel 同步对话路径")
    kernel_stream_path: str = Field(default="/chat/stream", description="Kernel 流式对话路径")

    # Domain Pack 配置
    flare_domain_pack_root: str = Field(default=".", description="domain-pack 根目录")
    upload_root: str = Field(default="/tmp/xiaocai-instance-uploads", description="上传文件存储根目录")
    storage_db_path: str = Field(default="/tmp/xiaocai-instance.db", description="SQLite 存储路径")
    storage_db_url: str = Field(default="", description="数据库连接串（优先，支持 postgresql://）")
    upload_max_size_bytes: int = Field(default=20 * 1024 * 1024, description="上传文件最大字节数")
    upload_allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx", "xls", "xlsx", "txt"],
        description="允许上传的文件扩展名",
    )
    enabled_modes: List[str] = Field(
        default=["auto", "requirement_canvas", "intelligent_sourcing"],
        description="允许的业务模式",
    )
    daily_message_limit: int = Field(default=0, description="每日消息上限，0 表示不限制")
    daily_project_message_limit: int = Field(default=0, description="每日单项目消息上限，0 表示不限制")

    # 认证配置
    mock_auth: bool = Field(default=True, description="是否使用 Mock 认证")
    real_auth_verify_url: str = Field(default="", description="真实认证验证 URL")
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
