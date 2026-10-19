"""Exercise a wheel's public authoring surface from an isolated temporary workspace."""

import argparse
import asyncio
import importlib.metadata
import importlib.resources
import importlib.util
import json
import os
import platform
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path


def cli(*arguments, stdin=None, status=0):
    console = Path(sys.executable).with_name("datamimic")
    result = subprocess.run(
        [str(console), *arguments], input=stdin, text=True, capture_output=True, timeout=90, check=False
    )
    assert result.returncode == status, (arguments, result.stdout, result.stderr)
    assert not result.stderr, (arguments, result.stderr)
    return result.stdout


async def check_mcp(schemas, request):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    console = Path(sys.executable).with_name("datamimic-mcp")
    launcher = Path.cwd() / "mcp launcher"
    launcher.mkdir()
    (launcher / "rows.csv").write_text("id|name\n0|WRONG_WORKSPACE\n", encoding="utf-8")
    transport = StdioTransport(
        command=str(console),
        args=["--transport", "stdio", "--workspace-root", str(Path.cwd())],
        cwd=str(launcher),
        env=dict(os.environ),
    )
    protocol_errors = []

    async def receive(message):
        if isinstance(message, Exception):
            protocol_errors.append(message)

    async with Client(transport, message_handler=receive) as client:
        tools = await client.list_tools()
        assert {item.name for item in tools} == {
            f"datamimic_{name}"
            for name in (
                "version",
                "schema",
                "capabilities",
                "capability",
                "reference",
                "compile",
                "decompile",
                "build",
                "lint",
                "dry_run",
                "run",
            )
        }
        for name, schema in schemas.items():
            result = await client.call_tool("datamimic_schema", {"name": name})
            assert json.loads(result[0].text) == schema, name
        result = await client.call_tool("datamimic_build", {"request": request})
        built = json.loads(result[0].text)
        assert built["outcome"] == "ready" and built["evidence"][0]["count"] == 2, built
        result = await client.call_tool(
            "datamimic_dry_run",
            {
                "request": {
                    "xml": '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered"/></setup>'
                }
            },
        )
        sourced = json.loads(result[0].text)
        assert sourced["ok"] and sourced["products"][0]["rows"][0] == {"id": "1", "name": "inside"}, sourced
    assert not protocol_errors, protocol_errors


def check_installed(with_mcp):
    import datamimic_ce
    from datamimic_ce.authoring import create_authoring_application

    forbidden = ("datamimic_ce.engine.runtime", "datamimic_ce.engine.io", "datamimic_ce.interfaces.mcp", "datamimic_ee")
    assert not any(name.startswith(forbidden) for name in sys.modules), "public import initialized runtime/transport"
    assert "fastmcp" not in sys.modules and "uvicorn" not in sys.modules
    if not with_mcp:
        assert importlib.util.find_spec("fastmcp") is None, "base wheel profile must exclude MCP"
        assert importlib.util.find_spec("uvicorn") is None, "base wheel profile must exclude HTTP transport"
    origin = Path(datamimic_ce.__file__).resolve()
    assert origin.is_relative_to(Path(sysconfig.get_paths()["purelib"]).resolve()), origin
    version = importlib.metadata.version("datamimic_ce")
    assert version

    from datamimic_ce.authoring.domain.requests import (
        AuthoringSchemaId,
        BuildRequestV4,
        CompileDocumentRequest,
        DecompileDocumentRequest,
        LintRequest,
        ReadyBuild,
        ReferenceRequest,
        ReferenceTopic,
        RunRequest,
    )
    from datamimic_ce.resources.api import demo_names, demo_root

    application = create_authoring_application(workspace_root=Path.cwd())
    schemas = {name.value: application.schema(name) for name in AuthoringSchemaId}
    assert len(schemas) == 13 and all(schemas.values())
    assert schemas["build_request_v4"]["properties"]["version"]["const"] == "4.0"
    snapshot = application.capabilities()
    assert snapshot.element_capabilities and snapshot.generator_capabilities
    capabilities = snapshot.to_dict()
    for topic in ReferenceTopic:
        assert application.reference(ReferenceRequest(topic=topic)).ok, topic

    request = BuildRequestV4.model_validate(
        {
            "document": {
                "root": {
                    "kind": "setup",
                    "properties": {"rng_seed": 7},
                    "children": [
                        {
                            "kind": "generate",
                            "properties": {"name": "rows", "count": 2},
                            "children": [
                                {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}}
                            ],
                        }
                    ],
                }
            }
        }
    )
    compiled = application.compile_document(CompileDocumentRequest(document=request.document))
    assert compiled.outcome == "ready", compiled
    restored = application.decompile_document(DecompileDocumentRequest(xml=compiled.artifact.compiled_xml))
    assert restored.outcome == "ready" and restored.document == compiled.artifact.document, restored
    built = application.build(BuildRequestV4(document=restored.document))
    assert isinstance(built, ReadyBuild), built
    assert built.artifact.ce_version == version
    assert built.evidence[0].count == 2 and built.evidence[0].rows == ({"id": 1}, {"id": 2})

    invalid = '<setup><generate count="1"/></setup>'
    lint = application.lint(LintRequest(xml=invalid))
    assert not lint.ok and lint.diagnostics and lint.diagnostics[0].ce_error is not None, lint
    failed = application.dry_run(RunRequest(xml='<setup><generate name="rows" source="missing.csv"/></setup>'))
    assert not failed.ok and failed.diagnostics and not failed.products, failed
    (Path.cwd() / "rows.csv").write_text("id|name\n1|inside\n2|second\n", encoding="utf-8")
    sourced = application.dry_run(
        RunRequest(xml=('<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered"/></setup>'))
    )
    assert sourced.ok and sourced.products[0].count == 2, sourced
    assert sourced.products[0].rows[0] == {"id": "1", "name": "inside"}
    spawned = application.dry_run(
        RunRequest(
            xml=(
                '<setup rngSeed="7"><generate name="rows" count="1">'
                '<key name="pid" script="os.getpid()"/></generate></setup>'
            )
        )
    )
    assert spawned.ok and spawned.products[0].rows[0]["pid"] != os.getpid(), spawned

    package = importlib.resources.files("datamimic_ce")
    assert package.joinpath("py.typed").is_file()
    assert package.joinpath("domains/shared/domain_data/common/country_US.csv").read_bytes()
    assert "demo-condition" in set(demo_names())
    assert b"<setup" in demo_root().joinpath("demo-condition/datamimic.xml").read_bytes()
    assert "demo-condition" in cli("demo", "list")
    assert json.loads(cli("authoring", "version")) == {"ce_version": version}
    assert json.loads(cli("authoring", "schema", "--name", "build_request_v4")) == schemas["build_request_v4"]
    assert json.loads(cli("authoring", "capabilities", "--full")) == capabilities
    assert json.loads(cli("authoring", "reference"))["topic"] == "overview"
    cli_built = json.loads(cli("authoring", "build", "-", stdin=request.model_dump_json()))
    assert cli_built["outcome"] == "ready" and cli_built["evidence"][0]["count"] == 2, cli_built
    assert not json.loads(cli("authoring", "lint", "-", stdin=invalid, status=1))["ok"]
    assert "fastmcp" not in sys.modules and "uvicorn" not in sys.modules
    if with_mcp:
        asyncio.run(asyncio.wait_for(check_mcp(schemas, request.model_dump(mode="json")), timeout=120))
    print(
        json.dumps(
            {
                "version": version,
                "python": platform.python_version(),
                "package": str(origin),
                "schemas": len(schemas),
                "rows": 2,
                "real_child": True,
                "mcp_tools": 11 if with_mcp else 0,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp", action="store_true", help="also exercise the installed MCP console over stdio")
    arguments = parser.parse_args()
    checkout = Path(__file__).resolve().parents[1]
    assert sys.flags.isolated, "run this probe with python -I"
    assert not any(Path(entry).resolve().is_relative_to(checkout) for entry in sys.path if entry)
    os.environ.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="datamimic-installed-check-") as directory:
        os.chdir(directory)
        assert not Path.cwd().is_relative_to(checkout)
        check_installed(arguments.mcp)


if __name__ == "__main__":
    main()
