from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REMOTE_BUILD_SCRIPT = ROOT / "deploy" / "scripts" / "remote-deploy-frontend-standalone.sh"
LOCAL_UPLOAD_SCRIPT = ROOT / "deploy" / "scripts" / "deploy-frontend-standalone-to-aliyun-xiaocai.sh"
ALIYUN_RELEASE_SCRIPT = ROOT / "deploy" / "scripts" / "release-to-aliyun-xiaocai.sh"
STANDALONE_NGINX_TEMPLATE = ROOT / "deploy" / "nginx" / "frontend-standalone-http.conf.template"


def test_remote_standalone_frontend_installs_domain_packs() -> None:
    text = REMOTE_BUILD_SCRIPT.read_text()

    assert 'DOMAIN_PACKS_DIR="$REPO_DIR/domain-packs"' in text
    assert "$DOMAIN_PACKS_DIR/xiaocai/app-profile.json" in text
    assert 'cp -a "$DOMAIN_PACKS_DIR" "$REMOTE_WEB_ROOT/domain-packs"' in text


def test_remote_standalone_frontend_does_not_start_new_nginx_on_reload_failure() -> None:
    text = REMOTE_BUILD_SCRIPT.read_text()

    assert "nginx -s reload || nginx" not in text
    assert "no new nginx process was started" in text


def test_local_standalone_upload_syncs_domain_packs() -> None:
    text = LOCAL_UPLOAD_SCRIPT.read_text()

    assert "REMOTE_WEB_ROOT=${REMOTE_WEB_ROOT:-/opt/1panel/apps/openresty/openresty/root}" in text
    assert 'DOMAIN_PACKS_DIR="$ROOT_DIR/domain-packs"' in text
    assert "$DOMAIN_PACKS_DIR/xiaocai/app-profile.json" in text
    assert "$REMOTE_WEB_ROOT/domain-packs" in text


def test_aliyun_release_deploys_to_active_openresty_root() -> None:
    text = ALIYUN_RELEASE_SCRIPT.read_text()

    assert "REMOTE_WEB_ROOT=${REMOTE_WEB_ROOT:-/opt/1panel/apps/openresty/openresty/root}" in text
    assert "REMOTE_WEB_ROOT='$REMOTE_WEB_ROOT'" in text


def test_standalone_nginx_does_not_fallback_domain_packs_to_index() -> None:
    text = STANDALONE_NGINX_TEMPLATE.read_text()

    assert "location /domain-packs/" in text
    assert "try_files $uri =404;" in text
