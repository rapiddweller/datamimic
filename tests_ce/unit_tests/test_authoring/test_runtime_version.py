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
    def __init__(self, name: str, text: str) -> None:
        self.name = name
        self._text = text

    def read_text(self, encoding: str) -> str:
        assert encoding == "utf-8"  # the architecture gate: a text read names its encoding
        return self._text


class _Distribution:
    version = "9.9.9"

    def __init__(self, direct_url: str | None) -> None:
        # A wheel from an index has other metadata files but no direct_url.json.
        self.files = [_File("RECORD", "x")] + ([] if direct_url is None else [_File("direct_url.json", direct_url)])


def _version(monkeypatch: pytest.MonkeyPatch, direct_url: str | None) -> RuntimeVersion:
    monkeypatch.setattr(metadata, "distribution", lambda name: _Distribution(direct_url))
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


def test_a_missing_distribution_gives_an_unknown_version_and_no_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> metadata.Distribution:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "distribution", missing)

    reported = create_authoring_application().version()

    assert reported.ce_version == "unknown" and type(reported) is RuntimeVersion
