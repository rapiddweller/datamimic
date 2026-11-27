# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""#693: the version result names the Python version and, for a git install only, the commit."""

import platform
from importlib import metadata

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.capabilities import GitRuntimeVersion, RuntimeVersion

_SHA = "0123456789abcdef0123456789abcdef01234567"


class _File:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def read_binary(self) -> bytes:
        return self._data


class _Distribution:
    version = "9.9.9"

    def __init__(self, direct_url: bytes | None) -> None:
        # A wheel from an index has other metadata files but no direct_url.json.
        self.files = [_File("RECORD", b"x")] + ([] if direct_url is None else [_File("direct_url.json", direct_url)])


def _version(monkeypatch: pytest.MonkeyPatch, direct_url: str | bytes | None) -> RuntimeVersion:
    data = direct_url.encode() if isinstance(direct_url, str) else direct_url
    monkeypatch.setattr(metadata, "distribution", lambda name: _Distribution(data))
    return create_authoring_application().version()


@pytest.mark.parametrize(
    ("direct_url", "commit"),
    [
        (f'{{"url": "https://x/y.git", "vcs_info": {{"vcs": "git", "commit_id": "{_SHA}"}}}}', _SHA),
        ('{"url": "file:///src", "dir_info": {"editable": true}}', None),  # editable install: no VCS
        (f'{{"vcs_info": {{"vcs": "hg", "commit_id": "{_SHA}"}}}}', None),  # not git
        ('{"vcs_info": {"vcs": "git"}}', None),  # no commit recorded: never guessed
        ('{"vcs_info": {"vcs": "git", "commit_id": ""}}', None),
        ('{"vcs_info": {"vcs": "git", "commit_id": 7}}', None),
        ('{"vcs_info": "git"}', None),
        ("[]", None),
        ("not json", None),
        (None, None),  # a wheel from an index has no direct_url.json
    ],
)
def test_the_commit_is_named_only_for_a_git_install_that_records_one(
    monkeypatch: pytest.MonkeyPatch, direct_url: str | None, commit: str | None
) -> None:
    reported = _version(monkeypatch, direct_url)

    assert reported.ce_version == "9.9.9"
    assert reported.python_version == platform.python_version()
    assert reported.build_protocol == "5.0"
    if commit is None:
        assert type(reported) is RuntimeVersion
        assert "commit" not in reported.model_dump()
    else:
        assert isinstance(reported, GitRuntimeVersion) and reported.commit == commit


@pytest.mark.parametrize(
    "direct_url",
    [
        b"\xff\xfe{}",  # not UTF-8 at all (#704)
        b'{"vcs_info": {"vcs": "git", "commit_id": "0123456789abcdef0123456789abcdef01234567"}, "note": "\xff"}',
    ],
)
def test_a_direct_url_that_is_not_utf8_gives_no_commit_and_no_error(
    monkeypatch: pytest.MonkeyPatch, direct_url: bytes
) -> None:
    reported = _version(monkeypatch, direct_url)

    assert reported.ce_version == "9.9.9" and type(reported) is RuntimeVersion


def test_a_missing_distribution_gives_an_unknown_version_and_no_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> metadata.Distribution:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "distribution", missing)

    reported = create_authoring_application().version()

    assert reported.ce_version == "unknown" and type(reported) is RuntimeVersion
