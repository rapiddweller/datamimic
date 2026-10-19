"""Both native clients install the same self-contained authoring skill."""

import json
import re
from pathlib import Path

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
