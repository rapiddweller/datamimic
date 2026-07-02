"""TDD for MIME-sniffable binary stubs and the payload+checksum DSL recipe.

Pain points addressed (researched): upload validators / MIME sniffers check magic
bytes and reject random noise; BLOB columns pair with checksum columns that must
stay consistent with the payload.
"""

import base64
import hashlib
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent

_MAGIC = {
    "pdf": (b"%PDF-", b"%%EOF"),
    "png": (b"\x89PNG\r\n\x1a\n", b""),
    "jpeg": (b"\xff\xd8\xff", b"\xff\xd9"),
    "zip": (b"PK\x03\x04", b""),
    "gif": (b"GIF89a", b""),
    "gzip": (b"\x1f\x8b\x08", b""),
}


def _run(filename: str) -> list[dict]:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["g"]


def test_mime_stubs_have_correct_magic_header_and_trailer():
    rows = _run("binary_mime.xml")
    assert len(rows) == 3
    for r in rows:
        for field, (header, trailer) in _MAGIC.items():
            blob = r[field]
            assert isinstance(blob, bytes)
            assert blob.startswith(header), f"{field}: wrong magic header {blob[:8]!r}"
            assert blob.endswith(trailer), f"{field}: missing trailer"
        assert 64 <= len(r["pdf"]) <= 128  # length bounds still hold with header+trailer
        assert len(r["png"]) == 64


def test_mime_stubs_are_seeded_reproducible():
    assert [r["pdf"] for r in _run("binary_mime.xml")] == [r["pdf"] for r in _run("binary_mime.xml")]


def test_unknown_mime_type_raises_with_supported_list():
    with pytest.raises(Exception, match=r"application/whatever.*[Ss]upported|[Ss]upported.*application/whatever"):
        _run("binary_mime_unknown.xml")


def test_mime_length_smaller_than_signature_raises():
    with pytest.raises(Exception, match=r"too short|at least"):
        _run("binary_mime_too_short.xml")


def test_checksum_and_base64_pairing_recipe():
    rows = _run("binary_checksum_recipe.xml")
    assert len(rows) == 4
    for r in rows:
        payload = r["payload"]
        assert r["sha256"] == hashlib.sha256(payload).hexdigest()  # pair stays consistent
        assert base64.b64decode(r["b64"]) == payload
