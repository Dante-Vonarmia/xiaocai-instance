import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


class TestXiaocaiPack(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT / "domain-packs" / "xiaocai"
        self.fields = load_yaml(self.root / "fields.yaml")
        self.workflow = load_yaml(self.root / "workflow.yaml")
        self.taxonomy = load_yaml(self.root / "taxonomy.yaml")

    def test_active_pack_files_are_present(self) -> None:
        self.assertTrue((self.root / "fields.yaml").exists())
        self.assertTrue((self.root / "workflow.yaml").exists())
        self.assertTrue((self.root / "taxonomy.yaml").exists())
        self.assertTrue((self.root / "templates" / "requirements-document.md").exists())

    def test_legacy_pack_directories_are_removed(self) -> None:
        legacy_dirs = [
            "schema",
            "cards",
            "category-fields",
            "activity_procurement",
            "gift_customization",
            "shared",
            "contracts",
            "workflows",
            "terminology",
        ]
        for name in legacy_dirs:
            with self.subTest(name=name):
                self.assertFalse((ROOT / "domain-packs" / name).exists())

    def test_xiaocai_pack_contract_markers(self) -> None:
        registry = {
            item["module_key"]: item
            for item in self.workflow.get("module_prompt_registry", [])
            if isinstance(item, dict) and item.get("module_key")
        }

        self.assertEqual(len(self.fields["field_definitions"]), 81)
        self.assertNotIn("寻源", self.taxonomy["intent_aliases"])
        self.assertNotIn("供应商", self.taxonomy["intent_aliases"])
        self.assertEqual(set(registry), {"requirement_intake", "analysis_mode"})
        self.assertEqual(registry["analysis_mode"]["action_commands"], ["generate_analysis", "confirm_plan"])


if __name__ == "__main__":
    unittest.main()
