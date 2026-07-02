# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator

# MIME type -> (magic header, trailer). The generated blob is header + random payload + trailer:
# a MIME-SNIFFABLE STUB that passes magic-byte upload validators / file-type sniffers - not a
# renderable document. The whole zip family (docx/xlsx/jar/apk) shares the PK header.
MIME_SIGNATURES: dict[str, tuple[bytes, bytes]] = {
    "application/pdf": (b"%PDF-1.4\n", b"\n%%EOF"),
    "image/png": (b"\x89PNG\r\n\x1a\n", b""),
    "image/jpeg": (b"\xff\xd8\xff\xe0", b"\xff\xd9"),
    "image/gif": (b"GIF89a", b""),
    "application/zip": (b"PK\x03\x04", b""),
    "application/gzip": (b"\x1f\x8b\x08", b""),
}


class BinaryGenerator(BaseLiteralGenerator):
    """Generate random ``bytes`` of a length in [min_len, max_len] (defaults 1..16).

    Backs ``<key type="binary" minLength=... maxLength=... [mimeType=...]>``. With ``mime_type`` the
    bytes start with the format's magic header (and end with its trailer where the format has one),
    so MIME sniffers and upload validators recognize them. Deterministic under a seeded rng
    (``rng.randbytes``). Raw bytes stay in the product (DBs take them natively); file exporters
    base64-encode them at the export boundary.
    """

    def __init__(
        self,
        min_len: int | None = None,
        max_len: int | None = None,
        mime_type: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(rng=rng)
        if mime_type is not None and mime_type not in MIME_SIGNATURES:
            raise ValueError(
                f"BinaryGenerator mimeType '{mime_type}' is not supported. "
                f"Supported: {', '.join(sorted(MIME_SIGNATURES))}"
            )
        self._header, self._trailer = MIME_SIGNATURES.get(mime_type, (b"", b""))  # type: ignore[arg-type]
        signature_len = len(self._header) + len(self._trailer)

        # One bound given -> the other defaults sensibly, mirroring StringGenerator.
        if min_len is None and max_len is None:
            # a mime stub defaults document-ish (64..256), plain bytes stay small (1..16)
            lo, hi = (64, 256) if mime_type else (1, 16)
        elif min_len is None:
            hi = int(max_len)  # type: ignore[arg-type]
            lo = min(1, hi)
        elif max_len is None:
            lo = hi = int(min_len)
        else:
            lo, hi = int(min_len), int(max_len)
        if lo < 0 or hi < 0:
            raise ValueError(f"BinaryGenerator lengths must be >= 0, got min={lo}, max={hi}")
        if lo > hi:
            raise ValueError(f"BinaryGenerator min length {lo} exceeds max length {hi}")
        if mime_type is not None and hi < signature_len:
            raise ValueError(
                f"BinaryGenerator maxLength {hi} is too short for mimeType '{mime_type}': "
                f"its signature needs at least {signature_len} bytes"
            )
        self._min_len = max(lo, signature_len)
        self._max_len = hi

    def generate(self) -> bytes:
        length = self.rng.randint(self._min_len, self._max_len)
        payload_len = length - len(self._header) - len(self._trailer)
        return self._header + self.rng.randbytes(payload_len) + self._trailer
