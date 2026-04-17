import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


def recommendation_level(score: int, hard_gates_passed: bool, veto_hit: bool) -> str:
    if (not hard_gates_passed) or score < 60 or veto_hit:
        return "淘汰"
    if score >= 80:
        return "推荐"
    return "谨慎"


class TestSupplierScorecard(unittest.TestCase):
    def test_activity_scorecard_outputs_valid_level(self) -> None:
        scorecard = load_yaml(
            ROOT / "domain-packs" / "activity_procurement" / "supplier_scorecard.yaml"
        )
        levels = {x.get("level") for x in scorecard.get("recommendation_levels", [])}

        for s in [90, 72, 40]:
            out = recommendation_level(s, True, False)
            self.assertIn(out, levels)

    def test_gift_scorecard_outputs_valid_level(self) -> None:
        scorecard = load_yaml(
            ROOT / "domain-packs" / "gift_customization" / "supplier_scorecard.yaml"
        )
        levels = {x.get("level") for x in scorecard.get("recommendation_levels", [])}

        out1 = recommendation_level(85, True, False)
        out2 = recommendation_level(65, True, False)
        out3 = recommendation_level(65, False, False)
        self.assertIn(out1, levels)
        self.assertIn(out2, levels)
        self.assertIn(out3, levels)


if __name__ == "__main__":
    unittest.main()
