# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Package only CE-owned, live DSL and Authoring contract projections."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from importlib.metadata import version
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import AuthoringSchemaId, ReferenceRequest, ReferenceTopic


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def build_contract_bundle_files(*, package_version: str, commit_sha: str) -> dict[str, bytes]:
    if package_version != version("datamimic_ce"):
        raise ValueError("package_version must match the installed CE distribution version")
    app = create_authoring_application()
    catalog = app.capabilities()
    producer = {"name": "datamimic-ce", "package_version": package_version, "commit_sha": commit_sha}
    envelope = {"schema_version": "1", "producer": producer}
    files = {
        "dsl-contract.json": _json_bytes(
            {
                **envelope,
                "elements": [element.model_dump(mode="json") for element in catalog.element_capabilities],
                "document_schema": app.schema(AuthoringSchemaId.DM_JSON_DOCUMENT_V1),
            }
        ),
        "authoring-capabilities.json": _json_bytes({**envelope, "capabilities": catalog.model_dump(mode="json")}),
        "authoring-schemas.json": _json_bytes(
            {**envelope, "schemas": {schema_id.value: app.schema(schema_id) for schema_id in AuthoringSchemaId}}
        ),
        "authoring-reference.json": _json_bytes(
            {
                **envelope,
                "topics": {
                    topic.value: app.reference(ReferenceRequest(topic=topic)).model_dump(mode="json")
                    for topic in ReferenceTopic
                },
            }
        ),
    }
    hashes = {name: hashlib.sha256(payload).hexdigest() for name, payload in sorted(files.items())}
    content = "".join(f"{name}\0{digest}\n" for name, digest in hashes.items()).encode("utf-8")
    files["manifest.json"] = _json_bytes(
        {**envelope, "files": hashes, "content_sha256": hashlib.sha256(content).hexdigest()}
    )
    return dict(sorted(files.items()))


def write_contract_bundle(output: Path, *, package_version: str, commit_sha: str) -> Path:
    files = build_contract_bundle_files(package_version=package_version, commit_sha=commit_sha)
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(content))
    compressed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as stream:
        stream.write(tar_buffer.getvalue())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(compressed.getvalue())
    return output
