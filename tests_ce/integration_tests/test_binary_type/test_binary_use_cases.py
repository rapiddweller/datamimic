"""Business use cases for native binary data, expressed entirely in the DSL.

UC1 document vault / KYC intake: BLOB content + mime type + content hash + size, format-recognizable
    stubs through a real DB write-and-verify plus a base64 JSON export.
UC2 key material: fixed-length IVs/keys/salts where exact byte lengths are the requirement.
Both are fully synthetic: generated from a seed, no source data is read.
"""

import base64
import hashlib
import json
import shutil
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent

_MAGIC = {"application/pdf": b"%PDF-", "image/png": b"\x89PNG", "image/jpeg": b"\xff\xd8\xff"}


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def _clean():
    shutil.rmtree(_DIR / "output", ignore_errors=True)
    for f in _DIR.glob("db/uc_*.sqlite"):
        f.unlink(missing_ok=True)


def test_document_vault_kyc_intake():
    _clean()
    try:
        result = _run("uc_document_vault.xml")
        docs = result["documents"]
        assert len(docs) == 10

        for d in docs:
            blob = d["content"]
            # upload-validator ready: the blob starts with the magic bytes its mime_type declares
            assert blob.startswith(_MAGIC[d["mime_type"]])
            # metadata columns consistent with the payload - the integrity chain DMS tests need
            assert d["content_sha256"] == hashlib.sha256(blob).hexdigest()
            assert d["size_bytes"] == len(blob) >= 128

        # the DB round-trip re-verifies every stored hash against the stored BLOB
        assert all(v["hash_ok"] for v in result["verify"])
        assert len(result["verify"]) == 10

        # the JSON export carries base64 (API transport form), decodable back to the exact payload
        json_rows = json.loads(next((_DIR / "output").rglob("*.json")).read_text())
        assert sorted(base64.b64decode(r["content"]) for r in json_rows) == sorted(d["content"] for d in docs)
    finally:
        _clean()


def test_document_vault_is_seed_reproducible():
    _clean()
    try:
        first = [d["content_sha256"] for d in _run("uc_document_vault.xml")["documents"]]
        _clean()
        second = [d["content_sha256"] for d in _run("uc_document_vault.xml")["documents"]]
        assert first == second  # same seed -> byte-identical documents -> identical hashes
    finally:
        _clean()


def test_key_material_exact_lengths():
    rows = _run("uc_key_material.xml")["secrets"]
    assert len(rows) == 6
    for r in rows:
        assert len(r["iv"]) == 16  # AES-128 IV
        assert len(r["hmac_key"]) == 32  # SHA-256 HMAC key
        assert len(r["salt"]) == 8
        assert base64.b64decode(r["iv_b64"]) == r["iv"]
