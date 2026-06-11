from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENV_TEMPLATE_PATHS = [
    ROOT / "deploy" / ".env.example",
    ROOT / "deploy" / ".env.production.example",
]


def test_env_templates_do_not_override_product_capability_modes() -> None:
    for env_path in ENV_TEMPLATE_PATHS:
        text = env_path.read_text()

        assert "ENABLED_MODES=" not in text
