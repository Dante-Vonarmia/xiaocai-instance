import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


class TestRealProcurementScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT / "domain-packs"
        self.scenario_dir = self.root / "contracts" / "scenarios"
        self.field_dictionary = load_yaml(
            self.root / "schema" / "procurement-field-dictionary.yaml"
        )
        self.analysis_rfx = load_yaml(
            self.root / "contracts" / "procurement-analysis-rfx-templates.yaml"
        )
        self.sourcing = load_yaml(
            self.root / "contracts" / "procurement-search-sourcing-replace.yaml"
        )

    def test_scenarios_have_acceptance_expectations(self) -> None:
        for scenario_path in self.scenario_dir.glob("*.yaml"):
            scenario = load_yaml(scenario_path)
            expected = scenario["expected"]

            with self.subTest(scenario=scenario_path.name):
                self.assertGreater(len(expected.get("missing_fields", [])), 0)
                self.assertGreater(len(expected.get("next_question_fields", [])), 0)
                self.assertIsInstance(expected.get("allow_analysis"), bool)
                score_range = expected.get("readiness_score_range", {})
                self.assertGreaterEqual(score_range.get("min", -1), 0)
                self.assertLessEqual(score_range.get("max", 2), 1)
                self.assertLessEqual(score_range["min"], score_range["max"])

    def test_scenario_references_are_traceable_to_contracts(self) -> None:
        field_names = {field["字段名称"] for field in self.field_dictionary["fields"]}
        analysis_titles = {
            section["title"]
            for section in self.analysis_rfx["analysis_template"]["sections"]
        }
        sourcing_titles = {
            section["title"]
            for section in self.sourcing["sourcing_output_template"]["sections"]
        }
        allowed_rfx_types = set(self.analysis_rfx["rfx_templates"]["allowed_types"])

        for scenario_path in self.scenario_dir.glob("*.yaml"):
            scenario = load_yaml(scenario_path)
            expected = scenario["expected"]
            output = expected["output_assertions"]

            field_refs = (
                expected.get("required_fields_present", [])
                + expected.get("missing_fields", [])
                + expected.get("next_question_fields", [])
                + expected.get("search", {}).get("target_fields", [])
            )

            with self.subTest(scenario=scenario_path.name):
                self.assertTrue(set(field_refs).issubset(field_names))
                self.assertTrue(set(output["analysis_sections"]).issubset(analysis_titles | sourcing_titles))
                self.assertIn(output["rfx_type"], allowed_rfx_types)


if __name__ == "__main__":
    unittest.main()
