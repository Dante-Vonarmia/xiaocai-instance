import subprocess
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


class TestActivityPack(unittest.TestCase):
    def test_activity_pack_validation_passes(self) -> None:
        script = ROOT / "scripts" / "validate_domain_packs.py"
        res = subprocess.run(
            [str(script), "--root", str(ROOT / "domain-packs")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, msg=res.stdout + "\n" + res.stderr)

    def test_missing_budget_should_block(self) -> None:
        qf = load_yaml(ROOT / "domain-packs" / "activity_procurement" / "question_flow.yaml")
        example = load_yaml(
            ROOT / "domain-packs" / "activity_procurement" / "examples" / "missing_budget.yaml"
        )
        inputs = example["inputs"]

        blocked = []
        for rule in qf.get("blocking_conditions", []):
            missing_any = rule.get("when_missing_any", [])
            if any(k not in inputs or inputs.get(k) in (None, "") for k in missing_any):
                blocked.extend(rule.get("block_actions", []))

        self.assertIn("requirement_analysis", blocked)
        self.assertIn("intelligent_sourcing", blocked)
        self.assertIn("rfx_recommendation", blocked)


if __name__ == "__main__":
    unittest.main()
