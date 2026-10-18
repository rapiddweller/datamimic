import hashlib
import json
import tarfile
from importlib.metadata import version

import pytest


def test_contract_bundle_has_reproducible_content_and_verified_hashes(tmp_path):
    from datamimic_ce.interfaces.bundle import write_contract_bundle
    first = write_contract_bundle(tmp_path / "first.tar.gz", package_version=version("datamimic_ce"), commit_sha="abc123")
    second = write_contract_bundle(tmp_path / "second.tar.gz", package_version=version("datamimic_ce"), commit_sha="abc123")
    assert first.read_bytes() == second.read_bytes()
    with tarfile.open(first) as archive:
        names = archive.getnames()
        assert names == sorted(set(names))
        payloads = {name: archive.extractfile(name).read() for name in names}
    manifest = json.loads(payloads["manifest.json"])
    assert manifest["producer"]["name"] == "datamimic-ce"
    assert manifest["producer"]["package_version"] == version("datamimic_ce")
    assert manifest["producer"]["commit_sha"] == "abc123"
    for name, digest in manifest["files"].items():
        assert hashlib.sha256(payloads[name]).hexdigest() == digest
    schemas = json.loads(payloads["authoring-schemas.json"])["schemas"]
    assert {"compile_document_request", "decompile_document_result", "build_request_v4", "ready_build", "diagnostic"} <= schemas.keys()
    dsl = json.loads(payloads["dsl-contract.json"])
    assert dsl["document_schema"] == schemas["dm_json_document_v1"]
    assert dsl["document_schema"]["$defs"]["DmJsonNode_KEY"]["x-datamimic-constraints"]
    assert b"datamimic_ee" not in b"".join(payloads.values())


def test_contract_bundle_cannot_claim_a_different_installed_version(tmp_path):
    from datamimic_ce.interfaces.bundle import write_contract_bundle
    with pytest.raises(ValueError, match="version"):
        write_contract_bundle(tmp_path / "wrong.tar.gz", package_version="invented", commit_sha="local")
