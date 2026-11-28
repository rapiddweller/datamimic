# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A Python library loaded by <execute> reaches Ready through Build when it passes the library check (#332)."""

import ast
import pickle
import shutil
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.bounded_executor import _decode_reply
from datamimic_ce.authoring.adapters.dryrun import _BoundedPolicyRefusal, _WorkerFailure, _refuse_unbounded_execute
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.authoring.domain.script_semantics import LibraryRefusalReason as Reason
from datamimic_ce.authoring.domain.script_semantics import python_library_refusal
from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import BoundedExecutionStrategy
from tests_ce.authoring_project import build_project

_MODELS = Path(__file__).resolve().parents[2] / "fixtures" / "authoring" / "bounded_python_library"


def _build(tmp_path: Path, filename: str):
    project = shutil.copytree(_MODELS, tmp_path / "project")
    return build_project(project, (_MODELS / filename).read_text(encoding="utf-8"), max_count=5)


@pytest.mark.parametrize("filename", ["execute_sql.xml", "execute_per_row.xml"])
def test_execute_outside_a_setup_level_python_library_is_refused_by_policy(tmp_path: Path, filename: str) -> None:
    result = _build(tmp_path, filename)
    assert result.outcome == "rejected"
    assert [item.code for item in result.diagnostics] == [AuthoringRuleId.UNSUPPORTED_BOUNDED_OPERATION]


@pytest.mark.parametrize(
    ("source", "seeded", "reason"),
    [
        ("import random\nLOADS = [random.random]\n", True, None),
        ("from datamimic_ce.domains.api import BaseLiteralGenerator\n", False, None),
        ("def f():\n    import random\n", False, None),
        ("def f():\n    import random\n", True, Reason.IMPORT_INSIDE_BODY_UNDER_SEED),
        ("class G:\n    def f(self):\n        from uuid import uuid4\n", True, Reason.IMPORT_INSIDE_BODY_UNDER_SEED),
        ("import subprocess\n", False, Reason.IMPORT_NOT_ADMITTED),
        ("from datamimic_ce.engine.io.api import database_count_table_length\n", False, Reason.IMPORT_NOT_ADMITTED),
        ("from . import sibling\n", False, Reason.IMPORT_NOT_ADMITTED),
        ("VALUE = eval('1')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("write = open\nwrite('/x', 'w')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("load = __import__\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("x = __builtins__['open']\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return globals()\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return f.__globals__\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return getattr(f, '__globals__')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("g = getattr\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return print.__self__.open('/x', 'w')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f(module):\n    return module.__import__('subprocess')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        (
            "def f():\n    return object.__getattribute__(f, '__glo' + 'bals__')\n",
            False,
            Reason.FILE_OR_DYNAMIC_CODE_BUILTIN,
        ),
        ("def f(o, n):\n    return getattr(o, '__' + n)\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("import random\nDATA = random.__loader__\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("from re import compile\nPATTERN = compile('a+')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("from re import compile as open\ndel open\nopen('/x')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("import re\nPATTERN = re.compile('a+')\n", False, None),
        ("import random\nB = random.__dict__['__builtins__']\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        (
            "import random\nB = getattr(random, '__dict__')['__builtins__']\n",
            False,
            Reason.FILE_OR_DYNAMIC_CODE_BUILTIN,
        ),
        ("class Row:\n    def as_dict(self):\n        return dict(self.__dict__)\n", False, None),
        ("def broken(:\n", False, None),
        ("VALUE = '__builtins__'\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("VALUE = '__globals__'\n", False, None),
        ("VALUE = '__Builtins__'\n", False, None),
        ("VALUE = ''\n", False, None),
        ("VALUE = b'__builtins__'\n", False, None),
    ],
)
def test_python_library_refusal(source: str, seeded: bool, reason: Reason | None) -> None:
    refusal = python_library_refusal(source, seeded=seeded)
    assert (refusal.reason if refusal else None) is reason


@pytest.mark.parametrize(("expression", "field"), [("name", "id"), ("obj.attr", "attr"), ("'text'", "value")])
def test_library_check_does_not_compare_or_hash_non_string_ast_fields(
    monkeypatch: pytest.MonkeyPatch, expression: str, field: str
) -> None:
    comparisons: list[str] = []

    class NonString:
        def __eq__(self, other: object) -> bool:
            comparisons.append("eq")
            return True

        def __hash__(self) -> int:
            comparisons.append("hash")
            return 0

    tree = ast.parse(expression, mode="eval")
    setattr(tree.body, field, NonString())
    with monkeypatch.context() as patch:
        patch.setattr(ast, "parse", lambda source: tree)
        refusal = python_library_refusal(expression, seeded=False)

    assert comparisons == []
    assert refusal is None


def test_refusal_names_the_earliest_line_and_no_source_text() -> None:
    refusal = python_library_refusal("SECRET = 'token-123'\nimport socket\nx = open('a')\n", seeded=False)
    assert refusal is not None and refusal.line == 2
    assert "token-123" not in refusal.message() and "socket" not in refusal.message()


@pytest.mark.parametrize("uri", ["/workspace/lib/unsafe.py", "lib/../unsafe.py"])
def test_library_refusal_location_uses_only_basename_for_unsafe_uri(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, uri: str
) -> None:
    from datamimic_ce.engine.dsl import api

    monkeypatch.setattr(api, "read_resource_bytes", lambda path: b"import socket\n")
    with pytest.raises(_BoundedPolicyRefusal) as raised:
        _refuse_unbounded_execute(
            "python",
            target=None,
            script=None,
            uri=uri,
            inline=None,
            setup_level=True,
            descriptor_dir=tmp_path,
            seeded=False,
        )
    refusal = raised.value
    message = _WorkerFailure(
        message=str(refusal),
        fix_hint="Repair the library.",
        policy_refusal=True,
        script_file=refusal.script_file,
        script_line=refusal.script_line,
    )
    request = BoundedExecutionRequest(xml="<setup/>", descriptor_path=PurePosixPath("datamimic.xml"))
    result = _decode_reply(pickle.dumps(message), request, tmp_path)
    assert result.diagnostics[0].location is not None
    assert result.diagnostics[0].location.script_file == "unsafe.py"
    assert result.diagnostics[0].location.script_line == 1


def test_published_execute_capability_names_the_library_strategy() -> None:
    capability = create_authoring_application(_MODELS).capability(CapabilityDomain.ELEMENT, "execute").capability
    assert capability.bounded_execution.strategy is BoundedExecutionStrategy.PYTHON_LIBRARY
