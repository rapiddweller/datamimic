# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Prepare plugin metadata from a published CE wheel."""

import argparse
import hashlib
import json
import os
import re
import tempfile
from email.parser import BytesParser
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (
    Path("plugins/datamimic/.codex-plugin/plugin.json"),
    Path("plugins/datamimic/.claude-plugin/plugin.json"),
)
MCP_FILE = Path("plugins/datamimic/.mcp.json")
RELEASE_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def source_index(args: list[str]) -> int:
    if args.count("--from") != 1 or args.index("--from") + 1 >= len(args):
        raise ValueError("The MCP server must have exactly one --from argument with a source.")
    return args.index("--from") + 1


def check_wheel(wheel: Path, tag: str) -> None:
    if RELEASE_VERSION.fullmatch(tag) is None:
        raise ValueError("The release tag must have the form X.Y.Z.")
    with ZipFile(wheel) as archive:
        metadata_paths = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_paths) != 1:
            raise ValueError("The wheel must contain exactly one metadata file.")
        metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))
    if metadata.get("Name", "").lower().replace("_", "-") != "datamimic-ce":
        raise ValueError("The wheel is not datamimic-ce.")
    if metadata["Version"] != tag:
        raise ValueError(f"Release versions differ: tag={tag}, wheel={metadata['Version']}.")


def check_published(wheel: Path, tag: str) -> None:
    with urlopen(f"https://pypi.org/pypi/datamimic-ce/{tag}/json", timeout=30) as response:
        release = json.load(response)
    with wheel.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if not any(
        item["filename"] == wheel.name and item["digests"]["sha256"] == digest and not item["yanked"]
        for item in release["urls"]
    ):
        raise ValueError("The wheel does not match an available file on PyPI.")


def prepare(root: Path, wheel: Path, tag: str) -> None:
    check_wheel(wheel, tag)
    check_published(wheel, tag)
    paths = tuple(root / name for name in (*MANIFESTS, MCP_FILE))
    documents = tuple(json.loads(path.read_text(encoding="utf-8")) for path in paths)
    for manifest in documents[:2]:
        manifest["version"] = tag
    args = documents[2]["mcpServers"]["datamimic"]["args"]
    args[source_index(args)] = f"datamimic-ce[mcp]=={tag}"
    written = []
    for path, document in zip(paths, documents, strict=True):
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
                temporary.write(json.dumps(document, indent=2) + "\n")
            os.chmod(temporary.name, path.stat().st_mode & 0o777)
            os.replace(temporary.name, path)
        except OSError as error:
            raise OSError(
                f"Could not write {path}; files already updated: {written}. Check all three files."
            ) from error
        written.append(str(path))


def verify(root: Path, wheel: Path, tag: str) -> None:
    check_wheel(wheel, tag)
    versions = [json.loads((root / path).read_text(encoding="utf-8"))["version"] for path in MANIFESTS]
    args = json.loads((root / MCP_FILE).read_text(encoding="utf-8"))["mcpServers"]["datamimic"]["args"]
    source = args[source_index(args)]
    if any(version != tag for version in versions) or source != f"datamimic-ce[mcp]=={tag}":
        raise ValueError(f"Plugin versions or source differ from {tag}: versions={versions}, source={source}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subcommands.add_parser("prepare")
    prepare_parser.add_argument("wheel", type=Path)
    prepare_parser.add_argument("tag")
    verify_parser = subcommands.add_parser("verify")
    verify_parser.add_argument("wheel", type=Path)
    verify_parser.add_argument("tag")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(ROOT, args.wheel, args.tag)
    else:
        verify(ROOT, args.wheel, args.tag)


if __name__ == "__main__":
    main()
