from pathlib import Path
import sys
import tempfile

import pytest


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from xiaocai_instance_api.settings import get_settings


@pytest.fixture(autouse=True)
def isolate_storage_env(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="xiaocai-test-storage-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        monkeypatch.setenv("STORAGE_DB_PATH", str(tmp_path / "instance.db"))
        monkeypatch.setenv("UPLOAD_ROOT", str(tmp_path / "uploads"))
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()
