"""Both native clients install the same self-contained authoring skill."""

import json
import re
import shlex
from pathlib import Path

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins/datamimic"


def test_native_manifests_identify_the_same_plugin() -> None:
    portable = json.loads((PLUGIN / "plugin.json").read_text())
    claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    assert portable["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert {key: portable[key] for key in ("name", "version", "description")} == {
        key: claude[key] for key in ("name", "version", "description")
    }
    assert portable["name"] == PLUGIN.name
    assert portable["extensions"]["com.openai"]["requires_local_executor"] is True
    assert len(portable["extensions"]["com.openai"]["interface"]["shortDescription"]) <= 30
    assert (PLUGIN / "skills/generate-test-data/SKILL.md").is_file()


def test_marketplace_resolves_the_packaged_plugin() -> None:
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(item for item in marketplace["plugins"] if item["name"] == PLUGIN.name)
    assert (ROOT / entry["source"]).resolve() == PLUGIN
    assert (ROOT / entry["source"] / "plugin.json").is_file()


def test_skill_references_are_available_without_a_datamimic_checkout() -> None:
    entrypoint = PLUGIN / "skills/generate-test-data/SKILL.md"
    assert entrypoint.is_file()
    documents = list(PLUGIN.rglob("*.md"))
    targets = []
    for document in documents:
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text()):
            path = target.partition("#")[0]
            if not path or "://" in path:
                continue
            resource = (document.parent / path).resolve()
            assert resource.is_relative_to(PLUGIN), target
            assert resource.is_file(), target
            targets.append(resource)
    assert targets, "The skill must carry its mode-specific guidance into foreign projects."


def test_onboarding_resolves_to_a_packaged_skill() -> None:
    manifest = json.loads((PLUGIN / "plugin.json").read_text())
    target = manifest["extensions"]["com.openai"]["onboardingSkill"]
    assert target.startswith("./")
    skill = (PLUGIN / target).resolve()
    assert skill.is_relative_to(PLUGIN)
    assert skill.parent.parent == PLUGIN / "skills"
    assert skill.name == "SKILL.md"
    assert skill.is_file()
    assert re.search(r"^name: " + re.escape(skill.parent.name) + r"$", skill.read_text(), re.MULTILINE)


def _command_lines() -> list[tuple[Path, list[str]]]:
    """Every `datamimic ...` command the plugin text tells an agent to run, as shell tokens."""
    found = []
    for document in [*PLUGIN.rglob("*.md"), ROOT / "docs/agent_plugin.md"]:
        text = document.read_text()
        blocks = re.findall(r"```\w*\n(.*?)```", text, re.DOTALL)
        spans = re.findall(r"`([^`\n]+)`", re.sub(r"```.*?```", "", text, flags=re.DOTALL))
        for line in [ln for block in blocks for ln in block.splitlines()] + spans:
            # A bare `authoring lint` span names the same CLI as `datamimic authoring lint`.
            line = f"datamimic {line}" if line.startswith("authoring ") else line
            if line.startswith("datamimic "):
                found.append((document, shlex.split(line)[1:]))
    return found


def test_every_command_the_plugin_names_exists_in_the_cli() -> None:
    from datamimic_ce.interfaces.cli._app import app

    commands = _command_lines()
    assert len(commands) >= 10, "The scan must find the plugin's commands."
    runner = CliRunner()
    for document, tokens in commands:
        # --help is eager: the parser still rejects an unknown command or option, and nothing executes.
        result = runner.invoke(app, [*tokens, "--help"])
        assert result.exit_code == 0, f"{document.relative_to(ROOT)}: datamimic {' '.join(tokens)}\n{result.output}"
