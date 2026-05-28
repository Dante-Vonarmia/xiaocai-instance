from xiaocai_instance_api.chat.kernel_client import KernelClient


def test_xiaocai_instance_kernel_body_injects_domain_binding_by_default():
    body = KernelClient._build_request_body(
        user_id="user-golden",
        message="帮我梳理采购需求",
        session_id="session-golden",
        context={"project_id": "project-golden"},
    )

    assert body["instance_id"] == "xiaocai"
    assert body["domain_pack_version"] == "default"
    assert body["payload"]["domain_pack_domain"] == "xiaocai"
    assert body["payload"]["instance_id"] == "xiaocai"
    assert body["payload"]["domain_pack_version"] == "default"


def test_xiaocai_instance_kernel_body_preserves_explicit_binding():
    body = KernelClient._build_request_body(
        user_id="user-golden",
        message="帮我梳理采购需求",
        session_id="session-golden",
        context={
            "instance_id": "tenant-x",
            "domain_pack_version": "v2",
            "domain_pack_domain": "tenant-domain",
        },
    )

    assert body["instance_id"] == "tenant-x"
    assert body["domain_pack_version"] == "v2"
    assert body["payload"]["domain_pack_domain"] == "tenant-domain"
    assert body["payload"]["instance_id"] == "tenant-x"
    assert body["payload"]["domain_pack_version"] == "v2"
