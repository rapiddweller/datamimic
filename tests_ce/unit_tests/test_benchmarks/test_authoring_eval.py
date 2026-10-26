# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The blind-agent eval oracle and transcript audit (#412): each reference project passes, each deliberately
broken variant fails exactly the checks it should, and the audit flags forbidden actions."""

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest

from benchmarks.authoring_eval.audit_transcript import FindingKind, audit
from benchmarks.authoring_eval.oracle import (
    CASES,
    ExactCount,
    ExactRows,
    FieldRef,
    Observed,
    PerParentCount,
    Repeatable,
    Unique,
    WholeNumber,
    evaluate,
    json_outputs,
)
from benchmarks.authoring_eval.run_subject import brief, isolation_problems

_ALL_CASES = sorted(path.name for path in CASES.iterdir() if path.is_dir())


@dataclass(frozen=True)
class Broken:
    """A reference project plus text edits (file -> [(old, new)]) and the check labels the oracle must fail."""

    case: str
    name: str
    edits: dict[str, list[tuple[str, str]]]
    fails: frozenset[str]


_XML = "datamimic.xml"
_ACCEPTANCE = "acceptance/build.json"

# Under PYTHONHASHSEED=1 this is 0 and under 2 it is 1 (CPython 3.11), which is what the oracle sets for its two runs.
_BOTH_OUTPUTS = frozenset({"output_rows:priced_orders:fixtures", "output_rows:priced_orders:fixtures_changed"})

_FLAG = "list({'alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel'}).index('bravo') % 2"


def _COUNTED(field: str, counter: str, script: str) -> tuple[str, str]:
    """Edit that turns an IncrementGenerator identifier into one built by ``script`` from a counter variable."""
    return (
        f'<key name="{field}" generator="IncrementGenerator"/>',
        f'<variable name="{counter}" generator="IncrementGenerator"/>\n        <key name="{field}" script="{script}"/>',
    )


_BROKEN = [
    Broken(
        "e01",
        "constant_ids",
        {_XML: [('name="ticket_id" generator="IncrementGenerator"', 'name="ticket_id" constant="7"')]},
        # constant= is text, and every title is the same "Ticket 7"
        frozenset({"unique:tickets.ticket_id", "whole_number:tickets.ticket_id", "unique:tickets.title"}),
    ),
    Broken(
        "e01",
        "constant_title",
        {_XML: [('string="Ticket __ticket_id__"', 'constant="Untitled"')]},
        frozenset({"unique:tickets.title"}),
    ),
    Broken(
        "e01",
        "priority_outside_set",
        {_XML: [("('LOW', 'MEDIUM', 'HIGH')", "('LOW', 'MEDIUM', 'HIGH', 'URGENT')")]},
        frozenset({"value_in:tickets.priority"}),
    ),
    # The agent's own acceptance agrees with the wrong count, so only the oracle can catch it.
    Broken(
        "e01",
        "weak_acceptance",
        {_XML: [('count="25"', 'count="24"')], _ACCEPTANCE: [('"count": 25', '"count": 24')]},
        frozenset({"exact_count:tickets"}),
    ),
    Broken(
        "e02",
        "colliding_invoice_ids",
        {_XML: [('script="parent.subscriber_id * 10 + invoice_no"', 'script="invoice_no"')]},
        frozenset({"unique:invoices.invoice_id", "build_ready"}),
    ),
    Broken(
        "e02",
        "hardcoded_foreign_key",
        {_XML: [('name="subscriber_id" script="parent.subscriber_id"', 'name="subscriber_id" script="1"')]},
        frozenset({"per_parent_count:invoices.subscriber_id", "build_ready"}),
    ),
    Broken(
        "e02",
        "two_invoices_per_subscriber",
        {
            _XML: [('<generate name="invoices" count="3">', '<generate name="invoices" count="2">')],
            _ACCEPTANCE: [('"count": 15', '"count": 10'), ('"count": 3', '"count": 2')],
        },
        frozenset({"exact_count:invoices", "per_parent_count:invoices.subscriber_id"}),
    ),
    Broken(
        "e03",
        "colliding_slot_ids",
        {_XML: [('script="parent.depot_id * 100 + token"', 'script="token"')]},
        frozenset({"exact_rows:slots", "build_ready"}),
    ),
    Broken(
        "e03",
        "token_in_output",
        {_XML: [('<variable name="token"', '<key name="token"')]},
        frozenset({"exact_rows:slots", "build_ready"}),
    ),
    Broken(
        "e03",
        "wrong_state",
        {_XML: [('constant="FREE"', 'constant="BUSY"')]},
        frozenset({"exact_rows:slots"}),
    ),
    Broken(
        "e04",
        "total_left_as_text",
        {_XML: [('script="int(source_row.total_cents)"', 'script="source_row.total_cents"')]},
        _BOTH_OUTPUTS,
    ),
    Broken(
        "e04",
        "wrong_priority_threshold",
        {_XML: [(">= 5000", ">= 4000")]},
        _BOTH_OUTPUTS,
    ),
    Broken(
        "e04",
        "no_json_target",
        {_XML: [(' target="JSON"', "")]},
        _BOTH_OUTPUTS,
    ),
    Broken(
        "e05",
        "independent_prices",
        {_XML: [('script="list_price * 8 // 10"', 'type="int" min="50" max="900"')]},
        frozenset({"field_at_most:offers.sale_price"}),
    ),
    Broken(
        "e05",
        "sale_price_below_floor",
        {_XML: [("list_price * 8 // 10", "list_price // 10")]},
        frozenset({"range:offers.sale_price"}),
    ),
    Broken(
        "e05",
        "tier_outside_set",
        {_XML: [("('BRONZE', 'SILVER', 'GOLD')", "('BRONZE', 'SILVER', 'GOLD', 'PLATINUM')")]},
        frozenset({"value_in:offers.tier"}),
    ),
    # --- seed and repeatability (the prompts prescribe a seed) ---
    *[
        Broken(case, "missing_seed", {_XML: [(f' rngSeed="{seed}"', "")]}, fails)
        for case, seed, fails in [
            ("e01", "10421", frozenset({"seed_is", "repeatable"})),
            ("e02", "30517", frozenset({"seed_is", "repeatable"})),
            ("e03", "56606", frozenset({"seed_is"})),  # no random draw, so unseeded runs still agree
            ("e04", "51110", frozenset({"seed_is"})),
            ("e05", "77031", frozenset({"seed_is", "repeatable"})),
        ]
    ],
    *[
        Broken(case, "wrong_seed", {_XML: [(f'rngSeed="{seed}"', 'rngSeed="1"')]}, frozenset({"seed_is"}))
        for case, seed in [("e01", "10421"), ("e02", "30517"), ("e03", "56606"), ("e04", "51110"), ("e05", "77031")]
    ],
    # The seed is right, but one value depends on the order of a set of strings. That order changes with the
    # interpreter's hash seed, so only a second run in a fresh interpreter shows it.
    Broken(
        "e01",
        "hash_ordered_hours",
        {_XML: [('name="estimate_hours" type="int" min="1" max="40"', f'name="estimate_hours" script="1 + {_FLAG}"')]},
        frozenset({"repeatable"}),
    ),
    Broken(
        "e02",
        "hash_ordered_amount",
        {
            _XML: [
                ('name="amount_cents" type="int" min="500" max="20000"', f'name="amount_cents" script="500 + {_FLAG}"')
            ]
        },
        frozenset({"repeatable"}),
    ),
    Broken(
        "e03",
        "hash_ordered_slot_ids",
        {
            _XML: [
                ('script="parent.depot_id * 100 + token"', f'script="parent.depot_id * 100 + token + 50 * ({_FLAG})"')
            ]
        },
        frozenset({"repeatable"}),
    ),
    Broken(
        "e04",
        "hash_ordered_priority",
        {
            _XML: [
                (
                    "script=\"'high' if int(source_row.total_cents) >= 5000 else 'standard'\"",
                    "script=\"('high' if int(source_row.total_cents) >= 5000 else 'standard') "
                    f"if {_FLAG} == 0 else 'unknown'\"",
                )
            ]
        },
        frozenset({"repeatable"}),
    ),
    Broken(
        "e05",
        "hash_ordered_sale_price",
        {_XML: [("list_price * 8 // 10", f"list_price * 8 // 10 + {_FLAG}")]},
        frozenset({"repeatable"}),
    ),
    # --- identifiers must be whole numbers ---
    Broken(
        "e01",
        "string_ticket_ids",
        {_XML: [_COUNTED("ticket_id", "ticket_no", "str(ticket_no)")]},
        frozenset({"whole_number:tickets.ticket_id"}),
    ),
    Broken(
        "e01",
        "float_ticket_ids",
        {_XML: [_COUNTED("ticket_id", "ticket_no", "float(ticket_no)")]},
        frozenset({"whole_number:tickets.ticket_id"}),
    ),
    Broken(
        "e02",
        "string_invoice_ids",
        {
            _XML: [
                (
                    'script="parent.subscriber_id * 10 + invoice_no"',
                    'script="str(parent.subscriber_id * 10 + invoice_no)"',
                )
            ]
        },
        frozenset({"whole_number:invoices.invoice_id"}),
    ),
    Broken(
        "e03",
        "string_slot_ids",
        {_XML: [('script="parent.depot_id * 100 + token"', 'script="str(parent.depot_id * 100 + token)"')]},
        frozenset({"exact_rows:slots"}),
    ),
    Broken(
        "e05",
        "string_offer_ids",
        {_XML: [_COUNTED("offer_id", "offer_no", "str(offer_no)")]},
        frozenset({"whole_number:offers.offer_id"}),
    ),
    Broken(
        "e05",
        "float_offer_ids",
        {_XML: [_COUNTED("offer_id", "offer_no", "float(offer_no)")]},
        frozenset({"whole_number:offers.offer_id"}),
    ),
]


# Whole wrong projects that a weak agent can write. Each one has the right shape and must still fail.
_CHEAT_ACCEPTANCE = '{"version": "5.0", "max_count": 15, "expectations": []}'
_CHEATS = {
    # slot_id from one counter over all slots, not from the depot and a counter inside it
    "e03": (
        """<setup rngSeed="56606">
    <generate name="depots" count="3">
        <key name="depot_id" generator="IncrementGenerator"/>
    </generate>
    <generate name="slots" count="12">
        <key name="slot_id" generator="IncrementGenerator"/>
        <key name="depot_id" script="(slot_id - 1) // 4 + 1"/>
        <key name="state" constant="FREE"/>
    </generate>
</setup>""",
        frozenset({"exact_rows:slots"}),
    ),
    # the six rows typed into scripts: the CSV is never read
    "e04": (
        """<setup rngSeed="51110">
    <generate name="priced_orders" count="6" target="JSON">
        <variable name="i" generator="IncrementGenerator"/>
        <key name="order_id" script="'O-' + str(99 + i)"/>
        <key name="customer_id" script="['C-10','C-11','C-10','C-12','C-13','C-14'][i - 1]"/>
        <key name="total_cents" script="[1200, 4500, 8000, 3200, 250, 9900][i - 1]"/>
        <key name="priority" script="'high' if total_cents >= 5000 else 'standard'"/>
    </generate>
</setup>""",
        frozenset({"output_rows:priced_orders:fixtures_changed"}),
    ),
}


@pytest.mark.parametrize("case", sorted(_CHEATS))
def test_cheat_project_fails_the_oracle(case: str, tmp_path: Path) -> None:
    xml, fails = _CHEATS[case]
    project = tmp_path / "project"
    (project / "acceptance").mkdir(parents=True)
    (project / _XML).write_text(xml, encoding="utf-8")
    (project / _ACCEPTANCE).write_text(_CHEAT_ACCEPTANCE, encoding="utf-8")

    assert _failed(project, case) == fails


def _failed(project: Path, case: str) -> set[str]:
    return {result.check for result in evaluate(case, project).checks if not result.passed}


def _reference(tmp_path: Path, case: str) -> Path:
    return shutil.copytree(CASES / case / "reference", tmp_path / "project")


@pytest.mark.parametrize("case", _ALL_CASES)
def test_reference_passes_every_check(case: str, tmp_path: Path) -> None:
    verdict = evaluate(case, _reference(tmp_path, case))

    assert [result for result in verdict.checks if not result.passed] == []
    assert verdict.passed


@pytest.mark.parametrize("broken", _BROKEN, ids=lambda broken: f"{broken.case}-{broken.name}")
def test_broken_variant_fails_exactly_the_expected_checks(broken: Broken, tmp_path: Path) -> None:
    project = _reference(tmp_path, broken.case)
    for filename, edits in broken.edits.items():
        text = (project / filename).read_text(encoding="utf-8")
        for old, new in edits:
            assert old in text, f"edit target missing from {filename}: {old}"
            text = text.replace(old, new)
        (project / filename).write_text(text, encoding="utf-8")

    assert _failed(project, broken.case) == broken.fails
    assert not evaluate(broken.case, project).passed


def test_output_file_left_by_the_agents_own_run_does_not_count(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e04")
    stale = project / "output" / "earlier-run"
    stale.mkdir(parents=True)
    (stale / "priced_orders.json").write_text(json.dumps([{}] * 6), encoding="utf-8")
    (project / _XML).write_text((project / _XML).read_text(encoding="utf-8").replace(' target="JSON"', ""))

    assert _failed(project, "e04") == _BOTH_OUTPUTS


def test_unreadable_output_files_are_skipped_not_a_crash(tmp_path: Path) -> None:
    (tmp_path / "output" / "run").mkdir(parents=True)
    (tmp_path / "output" / "run" / "broken.json").write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    (tmp_path / "output" / "run" / "object.json").write_text('{"a": 1}', encoding="utf-8")
    (tmp_path / "output" / "run" / "good.json").write_text("[1, 2]", encoding="utf-8")

    assert json_outputs(tmp_path) == {"good": [1, 2]}


def test_rows_that_json_cannot_encode_fail_the_check_but_do_not_crash() -> None:
    observed = Observed(None, None, {"p": [{"a": datetime(2026, 1, 1), "b": {1, 2}}]})

    assert ExactRows(kind="exact_rows", product="p", rows=[{"a": 1}]).failure(observed) is not None
    assert Unique(kind="unique", product="p", field="b").failure(observed) is not None


def test_every_case_has_broken_variants() -> None:
    assert {broken.case for broken in _BROKEN} == set(_ALL_CASES)


def test_oracle_ignores_the_agents_own_acceptance(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    (project / _ACCEPTANCE).write_text('{"version": "5.0", "expectations": []}', encoding="utf-8")
    (project / _XML).write_text((project / _XML).read_text(encoding="utf-8").replace('count="25"', 'count="3"'))

    assert "exact_count:tickets" in _failed(project, "e01")


def test_oracle_reports_a_missing_project_as_failed_checks(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    verdict = evaluate("e01", empty)

    assert not verdict.passed
    assert not any(result.passed for result in verdict.checks)


def test_verdict_carries_no_row_values(tmp_path: Path) -> None:
    text = evaluate("e04", _reference(tmp_path, "e04")).model_dump_json()

    assert "O-100" not in text
    assert "C-10" not in text


# --- transcript audit ---------------------------------------------------------------------------------------


def _line(*blocks: dict) -> str:
    return json.dumps({"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}})


def _call(name: str, **tool_input: str) -> dict:
    return {"type": "tool_use", "id": "t1", "name": name, "input": tool_input}


def _transcript(tmp_path: Path, *lines: str) -> Path:
    prompt = json.dumps({"type": "user", "message": {"role": "user", "content": "Do not read AGENTS.md."}})
    path = tmp_path / "agent.jsonl"
    path.write_text("\n".join([prompt, *lines]) + "\n", encoding="utf-8")
    return path


def _audit(transcript: Path, run: Path, venv: Path, canary: str | None = None) -> list[FindingKind]:
    allow = [run, venv / "bin" / "datamimic"]
    return [finding.kind for finding in audit(transcript, allow=allow, forbid=[Path("/repo")], canary=canary)]


def test_clean_transcript_has_no_findings(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(
        tmp_path,
        _line(_call("Bash", command=f"cd {run} && {venv}/bin/datamimic authoring build . | head -c 500")),
        _line(_call("Write", file_path=f"{run}/datamimic.xml", content="<setup/>")),
        _line(_call("Glob", pattern="**/*.xml", path=str(run))),
        _line({"type": "text", "text": "I read AGENTS.md"}),
    )

    assert _audit(transcript, run, venv, canary="canary-0123") == []


def test_reading_the_installed_source_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    source = f"{venv}/lib/python3.11/site-packages/datamimic_ce/__init__.py"

    assert _audit(_transcript(tmp_path, _line(_call("Read", file_path=source))), run, venv) == [
        FindingKind.OUTSIDE_ALLOWED
    ]


@pytest.mark.parametrize("tool", ["Skill", "WebFetch", "WebSearch", "Agent", "Task", "NotebookEdit"])
def test_tool_outside_the_allowlist_is_flagged(tool: str, tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"

    assert _audit(_transcript(tmp_path, _line(_call(tool, prompt="x"))), run, venv) == [FindingKind.TOOL]


def test_absolute_glob_pattern_outside_the_run_directory_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(tmp_path, _line(_call("Glob", pattern=f"{venv}/lib/**/*.py")))

    assert _audit(transcript, run, venv) == [FindingKind.OUTSIDE_ALLOWED]


def test_canary_anywhere_in_the_transcript_is_flagged(tmp_path: Path) -> None:
    """A relative `cat ../AGENTS.md` passes the path checks; its tool result still carries the token."""
    run, venv = tmp_path / "run", tmp_path / "venv"
    tool_result = {"type": "tool_result", "content": "canary-0123"}
    result = {"type": "user", "message": {"role": "user", "content": [tool_result]}}
    transcript = _transcript(tmp_path, _line(_call("Bash", command="cat ../AGENTS.md")), json.dumps(result))

    assert _audit(transcript, run, venv, canary="canary-0123") == [FindingKind.AGENTS_FILE, FindingKind.CANARY]


def test_xml_in_a_heredoc_is_not_a_path(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    command = f'cat > {run}/datamimic.xml <<\'EOF\'\n<setup>\n  <key name="x" constant="1"/>\n</setup>\nEOF'
    transcript = _transcript(tmp_path, _line(_call("Bash", command=command)))

    assert _audit(transcript, run, venv) == []


def test_repository_read_and_agents_file_are_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(tmp_path, _line(_call("Read", file_path="/repo/AGENTS.md")))

    assert set(_audit(transcript, run, venv)) == {
        FindingKind.AGENTS_FILE,
        FindingKind.FORBIDDEN_ROOT,
        FindingKind.OUTSIDE_ALLOWED,
    }


def test_shell_path_outside_the_run_directory_is_flagged(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    transcript = _transcript(tmp_path, _line(_call("Bash", command="cat /etc/hosts")))

    assert _audit(transcript, run, venv) == [FindingKind.OUTSIDE_ALLOWED]


def test_line_separator_inside_a_tool_call_does_not_split_a_record(tmp_path: Path) -> None:
    run, venv = tmp_path / "run", tmp_path / "venv"
    line = json.dumps(
        {"message": {"role": "assistant", "content": [_call("Bash", command="echo \u2028 /etc/hosts")]}},
        ensure_ascii=False,
    )

    assert _audit(_transcript(tmp_path, line), run, venv) == [FindingKind.OUTSIDE_ALLOWED]


# --- the new check kinds, one by one ---------------------------------------------------------------------------


def test_whole_number_rejects_bool_float_and_text() -> None:
    check = WholeNumber(kind="whole_number", product="p", field="id")

    assert check.failure(Observed(None, None, {"p": [{"id": 1}, {"id": 2}]})) is None
    for bad in (True, 1.0, "1", None):
        assert check.failure(Observed(None, None, {"p": [{"id": 1}, {"id": bad}]})) is not None


def test_whole_number_on_the_parent_key_is_what_catches_orphans() -> None:
    """unique + per_parent_count + exact_count prove that no child is an orphan only while the parent keys stay
    distinct as text: per_parent_count groups by str(), so the parents 1 and "1" merge and children 99 hide."""
    parents, children = FieldRef(product="p", field="id"), FieldRef(product="c", field="pid")
    observed = Observed(None, None, {"p": [{"id": 1}, {"id": "1"}], "c": [{"pid": v} for v in (1, 1, 99, 99)]})

    assert Unique(kind="unique", product="p", field="id").failure(observed) is None
    assert PerParentCount(kind="per_parent_count", child=children, parent=parents, n=2).failure(observed) is None
    assert ExactCount(kind="exact_count", product="c", n=4).failure(observed) is None
    assert WholeNumber(kind="whole_number", product="p", field="id").failure(observed) is not None


def test_repeatable_compares_the_second_run_in_order() -> None:
    check = Repeatable(kind="repeatable")
    rows = {"p": [{"a": 1}, {"a": 2}]}

    assert check.failure(Observed(None, None, rows, second_rows={"p": [{"a": 1}, {"a": 2}]})) is None
    assert check.failure(Observed(None, None, rows, second_rows={"p": [{"a": 2}, {"a": 1}]})) is not None
    assert check.failure(Observed(None, None, rows, second_error="Timeout")) is not None


def test_seed_is_reads_the_entry_descriptor_not_the_agents_acceptance_file(tmp_path: Path) -> None:
    project = _reference(tmp_path, "e01")
    (project / _ACCEPTANCE).write_text('{"version": "5.0", "expectations": [], "seed": 1}', encoding="utf-8")
    (project / _XML).write_text(
        (project / _XML).read_text(encoding="utf-8").replace('rngSeed="10421"', 'rngSeed="10421 "'), encoding="utf-8"
    )

    assert "seed_is" in _failed(project, "e01")


# --- the subject runner: the isolation checks ------------------------------------------------------------------

_TOKEN = "canary-0123"


@dataclass(frozen=True)
class _Run:
    base: Path
    run_dir: Path
    transcript: Path
    debug_log: Path

    @property
    def canary_files(self) -> list[Path]:
        return [self.base / "AGENTS.md", self.base / "CLAUDE.md"]


def _blind_run(tmp_path: Path, init: dict | None = None, result: dict | None = None, debug: str = "") -> _Run:
    """A transcript shaped like `claude -p --output-format stream-json` (key names from a real 2.1.304 run)."""
    run = _Run(tmp_path, tmp_path / "run", tmp_path / "transcript.jsonl", tmp_path / "debug.log")
    run.run_dir.mkdir()
    (run.run_dir / _XML).write_text("<setup/>", encoding="utf-8")
    records = [
        {
            "type": "system",
            "subtype": "init",
            "cwd": str(run.run_dir),
            "tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write"],
            "mcp_servers": [],
            "slash_commands": [],
            "skills": [],
            "plugins": [{"name": "installed-but-disabled"}],
        }
        | (init or {}),
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "terminal_reason": "completed",
            "permission_denials": [],
        }
        | (result or {}),
    ]
    run.transcript.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    run.debug_log.write_text("[DEBUG] $.fs.ancestors (cc-plugin-agents-md): project memory is off\n" + debug)
    return run


def _problems(run: _Run) -> list[str]:
    return isolation_problems(run.transcript, run.debug_log, run.run_dir, _TOKEN, run.canary_files)


def test_a_blind_run_has_no_isolation_problems(tmp_path: Path) -> None:
    assert _problems(_blind_run(tmp_path)) == []


@pytest.mark.parametrize(
    "change",
    [
        {"init": {"tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write", "WebFetch"]}},
        {"init": {"skills": ["generate-test-data"]}},
        {"init": {"mcp_servers": [{"name": "datamimic"}]}},
        {"init": {"slash_commands": ["compact"]}},
        {"init": {"subtype": "status"}},  # no init message at all
        {"result": {"is_error": True, "terminal_reason": "api_error"}},
        {"result": {"permission_denials": [{"tool_name": "Write"}]}},
        {"result": {"type": "assistant"}},  # no result message at all
        {"debug": '[DEBUG] "Hook SessionStart:startup success: {"additionalContext": "..."}"\n'},
    ],
)
def test_isolation_problem_is_reported(change: dict, tmp_path: Path) -> None:
    assert _problems(_blind_run(tmp_path, **change)) != []


def test_a_canary_file_named_in_the_debug_log_is_an_isolation_problem(tmp_path: Path) -> None:
    run = _blind_run(tmp_path)
    run.debug_log.write_text(f"[DEBUG] no CLAUDE.md found; AGENTS.md loaded: {run.canary_files[0]}\n")

    assert _problems(run) != []


def test_the_canary_in_a_file_of_the_run_directory_is_an_isolation_problem(tmp_path: Path) -> None:
    run = _blind_run(tmp_path)
    (run.run_dir / "notes.txt").write_text(f"code word {_TOKEN}", encoding="utf-8")

    assert _problems(run) != []


def test_a_cwd_other_than_the_run_directory_is_an_isolation_problem(tmp_path: Path) -> None:
    assert _problems(_blind_run(tmp_path, init={"cwd": str(tmp_path)})) != []


def test_the_brief_fills_every_placeholder(tmp_path: Path) -> None:
    text = brief("e01", tmp_path / "venv", tmp_path / "run")

    assert (CASES / "e01" / "prompt.md").read_text(encoding="utf-8") in text
    assert f"{tmp_path}/venv/bin/datamimic" in text
    assert not re.search(r"<(venv|run-dir|turn-limit|task)>", text)
