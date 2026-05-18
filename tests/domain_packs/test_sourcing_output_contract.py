import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


class TestSourcingOutputContract(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT / "domain-packs"
        self.sourcing_contract = load_yaml(
            self.root / "contracts" / "procurement-search-sourcing-replace.yaml"
        )
        self.field_dictionary = load_yaml(
            self.root / "schema" / "procurement-field-dictionary.yaml"
        )

    def test_sourcing_output_template_has_required_sections(self) -> None:
        template = self.sourcing_contract.get("sourcing_output_template", {})
        sections = template.get("sections", [])
        titles = [section["title"] for section in sections]

        self.assertEqual(
            titles,
            [
                "输入约束摘要",
                "候选池说明",
                "推荐理由",
                "风险提示",
                "下一步动作",
            ],
        )

    def test_sourcing_output_field_dependencies_are_traceable(self) -> None:
        field_names = {field["字段名称"] for field in self.field_dictionary["fields"]}
        sections = self.sourcing_contract.get("sourcing_output_template", {}).get("sections", [])

        self.assertGreater(len(sections), 0)
        for section in sections:
            with self.subTest(section=section["id"]):
                self.assertIn("required_fields", section)
                self.assertIn("optional_fields", section)
                self.assertIn("block_on_missing_required", section)
                self.assertIn("draft_allowed_when_missing", section)
                referenced_fields = set(section["required_fields"]) | set(section["optional_fields"])
                self.assertTrue(referenced_fields.issubset(field_names))


if __name__ == "__main__":
    unittest.main()
