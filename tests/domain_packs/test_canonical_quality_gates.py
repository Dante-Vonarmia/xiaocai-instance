import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


class TestCanonicalQualityGates(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT / "domain-packs"
        self.field_dictionary = load_yaml(
            self.root / "schema" / "procurement-field-dictionary.yaml"
        )
        self.procurement_schema = load_yaml(self.root / "schema" / "procurement.yaml")
        self.analysis_rfx = load_yaml(
            self.root / "contracts" / "procurement-analysis-rfx-templates.yaml"
        )

    def test_field_dictionary_count_and_source_are_frozen(self) -> None:
        contract = self.field_dictionary["contract"]
        fields = self.field_dictionary["fields"]
        names = [field["字段名称"] for field in fields]

        self.assertEqual(contract["field_count"], 81)
        self.assertEqual(len(fields), 81)
        self.assertEqual(len(set(names)), 81)
        self.assertIn("数据契约20260411.xlsx#总字段表", contract["source"])

    def test_stage_required_sets_match_quality_gate_counts(self) -> None:
        stage_sets = self.procurement_schema["stage_field_sets"]

        self.assertEqual(len(stage_sets["需求梳理必填集"]), 14)
        self.assertEqual(len(stage_sets["需求分析必填集"]), 17)
        self.assertEqual(len(stage_sets["RFX策略必填集"]), 33)

    def test_alias_and_derived_fields_are_explicitly_mapped(self) -> None:
        aliases = {
            item["external_name"]: item
            for item in self.field_dictionary.get("field_aliases", [])
        }

        expected = {
            "数量和单位": ("split", ["数量", "单位"]),
            "影响范围": ("alias", ["影响范围（部门/区域）"]),
            "供应商数量": ("alias", ["候选数量"]),
            "交期时长": ("derived", ["交付时间", "响应时效"]),
            "注册资金": ("alias", ["注册资本"]),
            "成立时长": ("derived", ["成立日期", "成立年份"]),
        }
        for external_name, (mapping_type, canonical_fields) in expected.items():
            with self.subTest(external_name=external_name):
                self.assertIn(external_name, aliases)
                self.assertEqual(aliases[external_name]["mapping_type"], mapping_type)
                self.assertEqual(aliases[external_name]["canonical_fields"], canonical_fields)

        for placeholder in ["对标企业", "员工规模", "实缴资金", "企业性质", "社保人数"]:
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, aliases)
                self.assertEqual(aliases[placeholder]["mapping_type"], "placeholder")
                self.assertFalse(aliases[placeholder]["readiness_gate"])

    def test_analysis_template_has_required_seven_sections(self) -> None:
        sections = self.analysis_rfx["analysis_template"]["sections"]
        titles = [section["title"] for section in sections]

        self.assertEqual(
            titles,
            [
                "项目理解与核心需求",
                "市场现状和分析",
                "成本结构分析",
                "项目风险分析",
                "采购策略分析",
                "供应商选择建议",
                "项目实施计划与执行建议",
            ],
        )

        for section in sections:
            with self.subTest(section=section["id"]):
                self.assertIn("required_fields", section)
                self.assertIn("optional_fields", section)
                self.assertIn("block_on_missing_required", section)
                self.assertIn("draft_allowed_when_missing", section)


if __name__ == "__main__":
    unittest.main()
