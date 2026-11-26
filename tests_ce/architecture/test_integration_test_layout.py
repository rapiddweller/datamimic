# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Guard the physical test lanes and their CI selection."""

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MOVED_NODE_DIGEST = "87acc25420514ee367d17e63fbc1a10b0460a2935b7af14511f957f63e6c2b9d"
MOVED = {
    "test_bounded_executor.py": {
        "test_timeout_terminates_worker_children_and_grandchildren",
        "test_timeout_stays_timeout_while_the_killed_group_is_still_exiting",
    },
    "test_bounded_python_library.py": {
        "test_library_function_reaches_ready_without_replay_when_unseeded",
        "test_seeded_library_loads_once_and_build_replays_it_unrequested",
        "test_library_check_refuses_before_the_library_runs",
        "test_entry_or_included_step_may_load_a_library",
        "test_included_library_is_checked_against_the_entry_seed",
        "test_forced_replay_names_why_a_seeded_library_model_failed",
        "test_library_outside_the_workspace_is_refused_not_loaded",
    },
    "test_build_verification.py": {
        "test_smoke_reuses_first_capture_and_real_json_exporter",
        "test_requested_smoke_without_exporter_is_not_applicable",
        "test_smoke_export_with_empty_nested_product",
        "test_capped_acceptance_cannot_be_rescued_by_replay",
        "test_dynamic_file_count_never_gets_exhaustion_proof",
        "test_literal_file_count_agrees_with_unmodified_runtime",
        "test_fixed_value_keeps_native_types_at_every_depth",
        "test_memstore_readback_uses_resolved_output_entity",
        "test_conditional_field_union_matches_unmodified_runtime",
    },
    "test_set_order_scan.py": {
        "test_the_replay_under_other_hash_seeds_rejects_each_s17_negative_and_names_a_cause",
        "test_mutant_replays_under_the_first_hash_seed_accept_each_s17_negative",
    },
}


def _integration_markers(source: str) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Attribute)
        and node.attr == "integration"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "pytest"
    ]


def _unit_shard_has_integration_path(workflow: str) -> bool:
    for job in ("unit_test_py314", "unit_coverage_shard"):
        section = re.split(r"\n  [a-zA-Z_][a-zA-Z_0-9]*:", workflow.split(f"  {job}:", 1)[1], maxsplit=1)[0]
        if "tests_ce/integration_tests" in section:
            return True
    return False


def test_unit_tree_has_no_integration_markers():
    for path in (ROOT / "tests_ce/unit_tests").rglob("*.py"):
        assert not _integration_markers(path.read_text(encoding="utf-8")), path


def test_moved_tests_exist_only_in_integration_or_nightly_modules():
    def definitions(path):
        return {
            node.name
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    for filename, names in MOVED.items():
        integration = ROOT / "tests_ce/integration_tests/test_authoring" / filename
        unit = ROOT / "tests_ce/unit_tests/test_authoring" / filename
        nightly = ROOT / "tests_ce/nightly_tests/test_authoring" / filename
        integration_names = definitions(integration)
        nightly_names = definitions(nightly) if nightly.exists() else set()
        assert names <= integration_names | nightly_names
        assert not names & integration_names & nightly_names
        assert not names & definitions(unit)
    assert (ROOT / "tests_ce/nightly_tests/test_benchmarks/test_authoring_eval.py").is_file()
    assert not (ROOT / "tests_ce/integration_tests/test_benchmarks/test_authoring_eval.py").exists()
    assert not (ROOT / "tests_ce/unit_tests/test_benchmarks/test_authoring_eval.py").exists()


def test_unit_ci_shards_do_not_select_integration_paths():
    assert not _unit_shard_has_integration_path((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))


def test_guards_reject_returned_marker_and_node_id():
    assert _integration_markers("pytestmark = [pytest.mark.integration]")
    workflow = (ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    mutant = workflow.replace(
        "tests_ce/unit_tests tests_ce/architecture",
        "tests_ce/integration_tests/test_authoring/test_build_verification.py"
        "::test_smoke_reuses_first_capture_and_real_json_exporter",
        1,
    )
    assert _unit_shard_has_integration_path(mutant)


def _moved_nodes_ok(nodes):
    return (
        len(nodes) == len(set(nodes)) == 279
        and hashlib.sha256(("\n".join(sorted(nodes)) + "\n").encode()).hexdigest() == MOVED_NODE_DIGEST
    )


def test_every_moved_parameterized_node_is_present_once():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-n",
            "0",
            "tests_ce/integration_tests/test_authoring/test_bounded_executor.py",
            "tests_ce/integration_tests/test_authoring/test_bounded_python_library.py",
            "tests_ce/integration_tests/test_authoring/test_build_verification.py",
            "tests_ce/integration_tests/test_authoring/test_set_order_scan.py",
            *(
                ["tests_ce/nightly_tests/test_authoring/test_build_verification.py"]
                if (ROOT / "tests_ce/nightly_tests/test_authoring/test_build_verification.py").exists()
                else []
            ),
            "tests_ce/nightly_tests/test_benchmarks",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    nodes = [
        line.replace(
            "tests_ce/nightly_tests/test_benchmarks/", "tests_ce/integration_tests/test_benchmarks/", 1
        ).replace("tests_ce/nightly_tests/test_authoring/", "tests_ce/integration_tests/test_authoring/", 1)
        for line in result.stdout.splitlines()
        if line.startswith(("tests_ce/integration_tests/", "tests_ce/nightly_tests/")) and "::" in line
    ]
    assert _moved_nodes_ok(nodes)
    assert not _moved_nodes_ok(nodes[:-1])
    assert not _moved_nodes_ok(nodes + [nodes[0]])


def _coverage_counts_match(workflow):
    for lane in ("unit", "integration", "functional"):
        shard = workflow["jobs"][f"{lane}_coverage_shard"]
        count = len(shard["strategy"]["matrix"]["include"])
        combine = workflow["jobs"][f"{lane}_test"]
        commands = "\n".join(step.get("run", "") for step in combine["steps"])
        match = re.search(r'wc -l\)" -eq (\d+)', commands)
        if match is None or int(match.group(1)) != count:
            return False
    return True


def test_ci_coverage_counts_match_matrices():
    workflow = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    assert _coverage_counts_match(workflow)
    workflow["jobs"]["integration_coverage_shard"]["strategy"]["matrix"]["include"].pop()
    assert not _coverage_counts_match(workflow)
    workflow = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    workflow["jobs"]["functional_coverage_shard"]["strategy"]["matrix"]["include"].pop()
    assert not _coverage_counts_match(workflow)


def _nightly_coverage_is_non_pr(workflow):
    covered = set()
    for lane in ("unit", "integration"):
        job = workflow["jobs"][f"{lane}_coverage_shard"]
        steps = job["steps"]
        pr_step = next(
            step for step in steps if step["name"] in ("Run unit tests in parallel", "Run integration tests")
        )
        if pr_step.get("if") != "github.event_name == 'pull_request' && matrix.pr":
            return False
        coverage_step = next(
            step
            for step in steps
            if step["name"] in ("Run unit tests with coverage", "Run integration tests with coverage")
        )
        if coverage_step.get("if") != "github.event_name != 'pull_request'":
            return False
        for shard in job["strategy"]["matrix"]["include"]:
            nightly = {arg for arg in shard["args"].split() if arg.startswith("tests_ce/nightly_tests/")}
            if type(shard.get("pr")) is not bool or (nightly and shard["pr"]):
                return False
            if not shard["pr"]:
                covered.update(nightly)
    expected = {path.relative_to(ROOT).as_posix() for path in (ROOT / "tests_ce/nightly_tests").rglob("test_*.py")}
    return covered == expected


def test_nightly_coverage_shards_do_not_run_on_prs():
    workflow = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    assert _nightly_coverage_is_non_pr(workflow)
    unit = workflow["jobs"]["unit_coverage_shard"]
    unit["strategy"]["matrix"]["include"][1]["pr"] = True
    assert not _nightly_coverage_is_non_pr(workflow)
    unit["strategy"]["matrix"]["include"][1]["pr"] = False
    next(step for step in unit["steps"] if step["name"] == "Run unit tests in parallel")["if"] = (
        "github.event_name == 'pull_request'"
    )
    assert not _nightly_coverage_is_non_pr(workflow)


def _forbidden_scenario_selection(text):
    return any(token in text for token in ("SCENARIO_" + "SHARD", "pytest_" + "deselected"))


def test_scenario_collection_is_not_filtered():
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "tests_ce", ".github/workflows"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    for name in tracked.split("\0"):
        path = ROOT / name
        if not name or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary test fixtures
        assert not _forbidden_scenario_selection(text), path
    assert _forbidden_scenario_selection("SCENARIO_" + "SHARD")
    assert _forbidden_scenario_selection("pytest_" + "deselected")


def test_scenarios_use_one_parallel_physical_coverage_shard():
    workflow = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["functional_coverage_shard"]
    shards = job["strategy"]["matrix"]["include"]
    assert [shard for shard in shards if "tests_ce/scenarios" in shard["args"]] == [
        {"shard": "scenarios", "args": "tests_ce/scenarios", "workers": "-n 4"}
    ]
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    assert "coverage run --parallel-mode -m pytest" in commands
    assert "${{ matrix.workers }}" in commands and "--cov --cov-report=" in commands


def test_precommit_unit_allowlist_is_exact():
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hooks = [hook for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == "precommit-unit"]
    assert len(hooks) == 1
    hook = hooks[0]
    assert hook["entry"] == "uv run --no-sync python -m pytest -n 2 -q"
    assert hook["pass_filenames"] is False and hook["always_run"] is True
    assert hook["args"] == ["tests_ce/unit_tests/precommit"]
    expected = {
        "test_limits.py::test_condition_branches_all_count_into_the_declared_total",
        "test_limits.py::test_source_free_children_of_a_source_parent_multiply_its_bound[source-parent-6-children-2]",
        "test_limits.py::test_source_free_children_of_a_source_parent_multiply_its_bound[two-levels-3-2-2]",
        "test_limits.py::test_source_free_children_of_a_source_parent_multiply_its_bound[source-parent-count-0]",
    }
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-n", "0", "tests_ce/unit_tests/precommit"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    prefix = "tests_ce/unit_tests/precommit/"
    nodes = [line.removeprefix(prefix) for line in collected.stdout.splitlines() if line.startswith(prefix)]
    assert len(nodes) == len(set(nodes)) and expected <= set(nodes)
    contracts = {
        "test_base_generator_hierarchy.py": "test_base_seeded_rng_yields_seeded_and_reproducible_rng",
        "test_date2timestamp_converter.py": "test_convert_invalid_type",
        "test_timestamp2date_converter.py": "test_convert_invalid_string_timestamp",
        "test_dm_json_codec_core.py": "test_rejects_lost_semantics_at_exact_paths",
        "test_error_pickling.py": "test_invalid_locale_error_round_trip_keeps_typed_fields_and_message",
        "test_expression_evaluation.py": "test_expression_errors_keep_messages_and_causes",
        "test_limits.py": "test_condition_branches_all_count_into_the_declared_total",
        "test_mask_converter.py": "test_mask_constructors_reject_non_single_character_strings",
        "test_min_max_count_validation.py": "test_min_max_count_malformed_strings_remain_validation_errors",
        "test_number_sequence_capacity.py": "test_finite_capacity_matches_runtime_iterator",
        "test_statement_scalar_types.py": "test_generator_model_rejects_missing_or_null_name",
        "test_task_util_semantics.py": "test_condition_evaluation_preserves_empty_boolean_and_invalid_rules",
        "test_uuid_generator.py": "test_uuid_generator_replays_with_same_seed",
        "test_value_literals.py": "test_every_other_unquoted_form_stays_an_error",
    }
    assert {path.name for path in (ROOT / prefix).glob("test_*.py")} == set(contracts)
    for filename, group in contracts.items():
        assert any(node.startswith(filename + "::") and group in node for node in nodes)


def test_no_obsolete_workflow_node_ids_or_automatic_scale_tests():
    workflows = list((ROOT / ".github/workflows").glob("*.yml"))
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        assert "tests_ce/unit_tests/test_benchmarks/test_authoring_eval.py" not in text, path
        for filename, names in MOVED.items():
            for name in names:
                assert f"tests_ce/unit_tests/test_authoring/{filename}::{name}" not in text, path
    main = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    shards = main["jobs"]["integration_coverage_shard"]["strategy"]["matrix"]["include"]
    for shard in shards:
        args = shard["args"].split()
        for arg in args:
            if "test_large_count" in arg and not arg.startswith("--ignore="):
                assert arg.rsplit("::", 1)[-1] in {"test_builders", "test_generators", "test_new_builders"}


def test_ci_matrices_use_paths_without_exclusion_filters():
    workflow = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    for job in (
        "unit_test_py314",
        "unit_coverage_shard",
        "functional_coverage_shard",
        "integration_coverage_shard",
        "external_service_shard",
    ):
        shards = workflow["jobs"][job]["strategy"]["matrix"]["include"]
        for shard in shards:
            args = shard["args"].split()
            assert not any(arg.startswith(("--ignore", "--deselect", "-k")) for arg in args), (job, args)
