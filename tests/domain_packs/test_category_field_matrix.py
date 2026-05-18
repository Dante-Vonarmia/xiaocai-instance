import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


def _category_paths(category_contract: dict) -> set[tuple[str, str]]:
    paths: set[tuple[str, str]] = set()
    for owner_group in category_contract.get("采购负责类", []):
        for level1 in owner_group.get("一级品类", []):
            level1_name = level1.get("名称")
            for level2 in level1.get("二级品类", []):
                level2_name = level2.get("名称")
                paths.add((level1_name, level2_name))
    return paths


def _field_names(field_dictionary: dict) -> set[str]:
    return {field["字段名称"] for field in field_dictionary.get("fields", [])}


class TestCategoryFieldMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT / "domain-packs"
        self.category_contract = load_yaml(
            self.root / "category-fields" / "procurement-category-fields.yaml"
        )
        self.field_dictionary = load_yaml(
            self.root / "schema" / "procurement-field-dictionary.yaml"
        )

    def test_directory_counts_and_source_are_frozen(self) -> None:
        directory = self.category_contract["directory"]
        paths = _category_paths(self.category_contract)
        level1_names = {
            level1["名称"]
            for owner_group in self.category_contract.get("采购负责类", [])
            for level1 in owner_group.get("一级品类", [])
        }

        self.assertIn("数据契约20260411.xlsx#品类维度的需求处理", directory["source"])
        self.assertEqual(directory["采购负责类数量"], len(self.category_contract["采购负责类"]))
        self.assertEqual(directory["一级品类数量"], len(level1_names))
        self.assertEqual(directory["二级品类数量"], len(paths))

    def test_default_field_matrix_is_traceable_to_field_dictionary(self) -> None:
        defaults = self.category_contract.get("field_matrix_defaults", {})
        field_names = _field_names(self.field_dictionary)

        self.assertEqual(defaults.get("required_fields"), [])
        self.assertEqual(defaults.get("required_fields_semantics"), "no_category_level_hard_gate")

        for bucket in ("identification_fields", "ranking_fields", "recommended_fields", "optional_fields"):
            with self.subTest(bucket=bucket):
                fields = defaults.get(bucket, [])
                self.assertIsInstance(fields, list)
                self.assertGreater(len(fields), 0)
                self.assertTrue(set(fields).issubset(field_names))

    def test_scenario_category_paths_exist_in_directory(self) -> None:
        paths = _category_paths(self.category_contract)
        scenario_dir = self.root / "contracts" / "scenarios"

        for scenario_path in scenario_dir.glob("*.yaml"):
            scenario = load_yaml(scenario_path)
            category_path = scenario["scenario"]["category_path"]
            key = (category_path["一级品类"], category_path["二级品类"])
            with self.subTest(scenario=scenario_path.name):
                self.assertIn(key, paths)


if __name__ == "__main__":
    unittest.main()
