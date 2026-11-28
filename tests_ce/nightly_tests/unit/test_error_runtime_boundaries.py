# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "body,expression,identity",
    [
        ('<generate name="rows" count="1"><array name="v" script="{expr}"/></generate>', "'{sentinel}'", "E013/I806"),
        (
            '<generate name="rows" count="1"><array name="v" script="{expr}"/></generate>',
            "[{{'{sentinel}': 1}}]",
            "E013/I804",
        ),
        (
            '<generate name="rows" count="1"><array name="v" script="{expr}"/></generate>',
            "['{sentinel}', 1]",
            "E013/I805",
        ),
        (
            '<generate name="rows" count="1"><nestedKey name="v" script="{expr}"/></generate>',
            "int('{sentinel}')",
            "E013/I832",
        ),
        (
            '<generate name="rows" count="1"><nestedKey name="v" script="{expr}"/></generate>',
            "'{sentinel}'",
            "E013/I815",
        ),
        (
            '<generate name="rows" count="1">'
            '<key name="v" script="os.environ[\'AUDIT_CALLER_SECRET\']"/><assert condition="False"/></generate>',
            "None",
            "E013/I895",
        ),
        ('<generate name="rows" count="1"><assert condition="{expr}"/></generate>', "int('{sentinel}')", "E013/I832"),
        (
            '<generate name="rows" count="{os.environ[\'AUDIT_CALLER_SECRET\']}">'
            '<key name="v" constant="ok"/></generate>',
            "None",
            "E013/I832",
        ),
        (
            '<generate name="rows" count="1"><key name="v" constant="ok" condition="{expr}"/></generate>',
            "'{sentinel}'",
            "E010/I507",
        ),
        ('<execute type="python" script="{expr}"/>', "len('{sentinel}')", "E013/I832"),
        (
            '<generate name="rows" count="1"><while condition="{expr}" maxIterations="1">'
            '<key name="v" constant="ok"/></while></generate>',
            "bool('{sentinel}')",
            "E013/I911",
        ),
        ('<variable name="v" entity="{expr}"/>', "{sentinel}", "E004"),
        ("<execute type=\"python\">import os\nint(os.environ['AUDIT_CALLER_SECRET'])</execute>", "None", "E013/I832"),
        ("<execute type=\"python\">import os\neval(os.environ['AUDIT_CALLER_SECRET'])</execute>", "None", "E013/I832"),
        ('<execute type="python">{sentinel}=1\nglobal {sentinel}</execute>', "None", "E013/I832"),
    ],
)
def test_expression_consumers_keep_runtime_values_private(tmp_path, body, expression, identity):
    sentinel = "AUDIT_ALL_CALLERS_PRIVATE_b4d7"
    path = tmp_path / "model.xml"
    path.write_text('<setup rngSeed="7">' + body.replace("{sentinel}", sentinel) + "</setup>")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "datamimic_ce.interfaces.cli",
            "run",
            str(path),
            "--param-env",
            "expr=AUDIT_CALLER_EXPRESSION",
            "--test-mode",
        ],
        env={
            **os.environ,
            "AUDIT_CALLER_EXPRESSION": expression.format(sentinel=sentinel),
            "AUDIT_CALLER_SECRET": sentinel,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert identity in output
    assert sentinel not in output
    assert "Traceback" not in output
