# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Stable descriptor identity independent of XML formatting."""

import json
from hashlib import sha256

from .dm_json import DmJsonDocumentV1


def canonical_dm_json(document: DmJsonDocumentV1) -> str:
    return json.dumps(document.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def semantic_fingerprint(document: DmJsonDocumentV1) -> str:
    return sha256(canonical_dm_json(document).encode("utf-8")).hexdigest()
