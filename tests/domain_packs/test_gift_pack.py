import subprocess
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


class TestGiftPack(unittest.TestCase):
    def test_gift_pack_validation_passes(self) -> None:
        script = ROOT / "scripts" / "validate_domain_packs.py"
        res = subprocess.run(
            [str(script), "--root", str(ROOT / "domain-packs")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, msg=res.stdout + "\n" + res.stderr)

    def test_tight_deadline_triggers_escalation_pattern(self) -> None:
        qf = load_yaml(ROOT / "domain-packs" / "gift_customization" / "question_flow.yaml")
        example = load_yaml(
            ROOT / "domain-packs" / "gift_customization" / "examples" / "tight_deadline.yaml"
        )
        inputs = example["inputs"]

        escalation_ids = [x.get("escalation_id") for x in qf.get("escalation_rules", [])]
        self.assertIn("GIFT-ESC-001", escalation_ids)
        self.assertEqual(inputs.get("customization_depth"), "深度定制")
        self.assertEqual(inputs.get("urgency"), "critical")


if __name__ == "__main__":
    unittest.main()
