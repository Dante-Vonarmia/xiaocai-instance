from scripts.check_flare_dependency_versions import (
    check_flare_dependency_versions,
    drifted_dependencies,
)


def test_local_flare_runtime_packages_match_pinned_versions():
    results = check_flare_dependency_versions()
    drifted = drifted_dependencies(results)

    assert not drifted, [result.to_dict() for result in drifted]
