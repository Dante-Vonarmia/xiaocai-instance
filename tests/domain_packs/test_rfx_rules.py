import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_packs import load_yaml  # type: ignore


def choose_rfx_action(signals: dict, rules: dict) -> str:
    for cond in rules.get("decision_conditions", []):
        when = cond.get("when", {})
        matched = True
        for key, val in when.items():
            if signals.get(key) != val:
                matched = False
                break
        if matched:
            return cond.get("recommended_action")
    return "RFP"


class TestRfxRules(unittest.TestCase):
    def test_rfx_rules_cover_reasonable_actions(self) -> None:
        rfx = load_yaml(ROOT / "domain-packs" / "shared" / "rules" / "rfx_rules.yaml")

        a1 = choose_rfx_action(
            {"requirement_clarity": "low", "supplier_market_maturity": "unknown_or_low"}, rfx
        )
        a2 = choose_rfx_action(
            {"requirement_clarity": "medium", "customization_level": "medium_or_high"}, rfx
        )
        a3 = choose_rfx_action(
            {
                "requirement_clarity": "high",
                "customization_level": "low_or_medium",
                "supplier_market_maturity": "high",
            },
            rfx,
        )
        a4 = choose_rfx_action(
            {"compliance_level": "high", "budget_level": "high"}, rfx
        )

        self.assertEqual(a1, "RFI")
        self.assertEqual(a2, "RFP")
        self.assertEqual(a3, "RFQ")
        self.assertEqual(a4, "RFB")


if __name__ == "__main__":
    unittest.main()
