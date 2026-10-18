"""Decoded XML must retain its text through an actual bounded Build."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.requests import BuildRequestV4, ReadyBuild


@pytest.mark.parametrize(
    "declaration", ["", '<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="ISO-8859-1"?>']
)
def test_decompiled_unicode_reaches_the_real_build_unchanged(tmp_path: Path, declaration: str) -> None:
    document = CeDmJsonCodec().decompile(
        declaration + '<setup rngSeed="7"><generate name="rows" count="1">'
        '<key name="value" constant="café"/></generate></setup>'
    )
    result = create_authoring_application(workspace_root=tmp_path).build(BuildRequestV4(document=document))

    assert isinstance(result, ReadyBuild), result
    assert result.evidence[0].rows == ({"value": "café"},)
