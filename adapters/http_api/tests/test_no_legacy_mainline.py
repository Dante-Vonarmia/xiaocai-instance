import json
import importlib.util

import xiaocai_instance_api.chat.router as router_module
from xiaocai_instance_api.chat.orchestration.contract_loader import (
    load_contracts,
    load_pack_mount_snapshot,
)
from xiaocai_instance_api.settings import get_settings


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _clear_cached_contracts():
    get_settings.cache_clear()
    load_contracts.cache_clear()
    load_pack_mount_snapshot.cache_clear()


def test_contract_loader_reads_xiaocai_pack_instead_of_legacy_schema(tmp_path, monkeypatch):
    pack_root = tmp_path / "domain-packs"
    _write_json(
        pack_root / "xiaocai" / "fields.yaml",
        {
            "required_fields": ["采购目的"],
            "field_definitions": [{"key": "采购目的", "label": "采购目的"}],
            "module_field_sets": {"需求分析": {"required_fields": ["采购目的"]}},
        },
    )
    _write_json(
        pack_root / "xiaocai" / "workflow.yaml",
        {"blocker_policies": {"required_fields": ["采购目的"]}},
    )
    _write_json(
        pack_root / "xiaocai" / "taxonomy.yaml",
        {"procurement_categories": {"活动执行": {}}},
    )
    _write_json(
        pack_root / "schema" / "fields.yaml",
        {"field_definitions": [{"key": "旧字段", "label": "旧字段"}]},
    )

    monkeypatch.setenv("FLARE_DOMAIN_PACK_ROOT", str(tmp_path))
    _clear_cached_contracts()

    contracts = load_contracts()

    assert "采购目的" in contracts.field_metadata
    assert "旧字段" not in contracts.field_metadata

    _clear_cached_contracts()


def test_router_does_not_expose_local_pending_contract_builder():
    assert not hasattr(router_module, "_build_pending_contract")
    assert importlib.util.find_spec("xiaocai_instance_api.chat.patch_contract") is None
