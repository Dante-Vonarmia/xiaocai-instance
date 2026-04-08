"""
迁移命令入口
"""

from xiaocai_instance_api.settings import get_settings
from xiaocai_instance_api.storage.migrations import run_storage_migrations


def main() -> None:
    settings = get_settings()
    version = run_storage_migrations(
        db_path=settings.storage_db_path,
        db_url=settings.storage_db_url,
    )
    backend = "postgres" if settings.storage_db_url.strip() else "sqlite"
    print(f"[xiaocai-db-migrate] backend={backend} version={version}")


if __name__ == "__main__":
    main()

