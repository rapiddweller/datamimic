"""Verify the fixed experiment archive without executing its contents."""

import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

root = Path(__file__).resolve().parent
archive = root / "experiment-documents-and-evidence.zip"
expected, filename = (root / "SHA256SUMS").read_text().strip().split()
assert filename == archive.name
with archive.open("rb") as stream:
    observed = hashlib.sha256(stream.read()).hexdigest()
assert observed == expected, "ZIP checksum mismatch"

with ZipFile(archive) as packet:
    records = json.loads(packet.read("manifest.json"))["records"]
    names = packet.namelist()
    assert len(names) == len(set(names)), "duplicate ZIP member"
    assert set(names) == {record["archive_path"] for record in records} | {"manifest.json"}
    for record in records:
        name = record["archive_path"]
        path = PurePosixPath(name)
        assert not path.is_absolute() and ".." not in path.parts, "unsafe member path"
        assert path.suffix.lower() not in {".html", ".htm", ".zip", ".gz", ".tar", ".whl", ".png", ".svg"}, name
        assert record["category"] != "source_snapshot", name
        assert packet.getinfo(name).file_size == record["size"], name
        with packet.open(name) as stream:
            digest = hashlib.sha256(stream.read()).hexdigest()
        assert digest == record["sha256"], name

print(f"Verified {len(records)} payloads, exact member set and ZIP checksum.")
