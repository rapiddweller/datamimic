# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Guard the physical test lanes and their CI selection."""

import ast
import copy
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PLATFORM_NODE_SELECTIONS = {
    "tests_ce/unit_tests/test_architecture_study_oracle.py",
    "tests_ce/unit_tests/test_authoring/test_dm_json_codec.py",
    "tests_ce/unit_tests/test_authoring/test_init.py",
    "tests_ce/unit_tests/test_authoring/test_ready_coverage.py",
    "tests_ce/unit_tests/test_authoring/test_project_run.py",
    "tests_ce/unit_tests/test_mcp/test_init_tool.py",
    "tests_ce/unit_tests/test_authoring/test_build_verification.py",
    "tests_ce/integration_tests/test_authoring/test_build_verification.py",
    "tests_ce/integration_tests/test_authoring/test_set_order_scan.py",
    "tests_ce/scenarios/test_scenarios.py",
}
LANES = {
    "precommit": ["tests_ce/unit_tests/precommit"],
    "unit": ["tests_ce/unit_tests"],
    "integration": ["tests_ce/integration_tests"],
    "nightly": ["tests_ce/nightly_tests"],
    "manual_perf": ["tests_ce/manual_perf_tests"],
    "functional": ["tests_ce/functional_tests", "tests_ce/conformance", "tests_ce/scenarios"],
    "architecture": ["tests_ce/architecture"],
}
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


def _collect_nodes(paths):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-n", "0", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.startswith("tests_ce/") and "::" in line]


def _inventory_matches(actual, expected):
    return len(actual) == len(set(actual)) == len(expected) == len(set(expected)) and set(actual) == set(expected)


def _automatic_makefile_paths_match(text):
    match = re.search(r"^AUTOMATIC_TESTS\s*:=\s*\$\(addprefix \$\(TESTS\)/,([^)]*)\)\s*$", text, re.MULTILINE)
    if match is None:
        return False
    selected = match.group(1).split()
    excluded = {"manual_perf_tests", "nightly_tests", "external_service_tests"}
    suites = {
        path.name
        for path in (ROOT / "tests_ce").iterdir()
        if path.is_dir() and next(path.rglob("test_*.py"), None) is not None
    }
    return len(selected) == len(set(selected)) and set(selected) == suites - excluded


def test_makefile_automatic_paths_cover_regular_suites():
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert _automatic_makefile_paths_match(text)
    assert not _automatic_makefile_paths_match(text.replace(" api_tests", "", 1))
    assert not _automatic_makefile_paths_match(text.replace(" factory_tests", "", 1))
    assert not _automatic_makefile_paths_match(text.replace(" api_tests", " api_tests manual_perf_tests", 1))


class _StrictWorkflowLoader(yaml.SafeLoader):
    pass


def _strict_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError(
                "mapping", node.start_mark, f"duplicate key {key!r}", key_node.start_mark
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictWorkflowLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_mapping)


def _strict_workflow(text):
    return yaml.load(text, Loader=_StrictWorkflowLoader)


def test_workflow_yaml_has_no_duplicate_mapping_keys():
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        _strict_workflow(path.read_text(encoding="utf-8"))
    with pytest.raises(yaml.constructor.ConstructorError, match="duplicate key"):
        _strict_workflow(
            "jobs:\n  x:\n    steps:\n      - uses: actions/checkout@v5\n        with: {}\n        with: {}\n"
        )


def _guard_jobs_have_full_checkout(workflow):
    for job in workflow["jobs"].values():
        steps = job.get("steps", [])
        commands = "\n".join(step.get("run", "") for step in steps)
        matrix = job.get("strategy", {}).get("matrix", {}).get("include", [])
        selections = commands + "\n" + "\n".join(shard.get("args", "") for shard in matrix)
        runs_guard = (
            "tests_ce/architecture/test_integration_test_layout.py" in selections
            or re.search(r"tests_ce/architecture(?=\s|$)", selections) is not None
            or "make test-architecture" in selections
        )
        if runs_guard and not any(
            step.get("uses", "").startswith("actions/checkout@") and step.get("with", {}).get("fetch-depth") == 0
            for step in steps
        ):
            return False
    return True


def test_guard_jobs_fetch_parent_history():
    workflow = _strict_workflow((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    assert _guard_jobs_have_full_checkout(workflow)
    checkout = next(
        step
        for step in workflow["jobs"]["windows_pr_tests"]["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
    )
    del checkout["with"]["fetch-depth"]
    assert not _guard_jobs_have_full_checkout(workflow)


def _ci_lane_paths(workflow):
    jobs = workflow["jobs"]
    paths = {}
    for lane in ("unit", "integration"):
        shards = jobs[f"{lane}_coverage_shard"]["strategy"]["matrix"]["include"]
        paths[lane] = [arg for shard in shards if shard["pr"] for arg in shard["args"].split()]
    paths["nightly"] = [
        arg
        for lane in ("unit", "integration")
        for shard in jobs[f"{lane}_coverage_shard"]["strategy"]["matrix"]["include"]
        if not shard["pr"]
        for arg in shard["args"].split()
    ]
    paths["functional"] = [
        arg
        for shard in jobs["functional_coverage_shard"]["strategy"]["matrix"]["include"]
        for arg in shard["args"].split()
    ]
    return paths


def _fixed_test_paths(command):
    return [arg for arg in shlex.split(command) if arg.startswith("tests_ce/")]


def test_ci_paths_cover_manifest_lanes():
    workflow = _strict_workflow((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "tests_ce/fixtures/lane_manifest.json").read_text(encoding="utf-8"))
    for lane in ("unit", "integration", "functional"):
        job = workflow["jobs"][f"{lane}_coverage_shard"]
        test_steps = [
            step
            for step in job["steps"]
            if "pytest" in step.get("run", "") or "coverage-unit-run" in step.get("run", "")
        ]
        assert test_steps and all("${{ matrix.args }}" in step["run"] for step in test_steps)
    paths = _ci_lane_paths(workflow)
    for lane, selected in paths.items():
        assert _inventory_matches(_collect_nodes(selected), manifest["lanes"][lane]), lane
    mutant = copy.deepcopy(workflow)
    mutant["jobs"]["unit_coverage_shard"]["strategy"]["matrix"]["include"][0]["args"] = "tests_ce/unit_tests/precommit"
    assert not _inventory_matches(_collect_nodes(_ci_lane_paths(mutant)["unit"]), manifest["lanes"]["unit"])

    architecture = next(
        step["run"]
        for step in workflow["jobs"]["architecture_tests"]["steps"]
        if step.get("name") == "Run architecture tests"
    )
    assert _inventory_matches(_collect_nodes(_fixed_test_paths(architecture)), manifest["lanes"]["architecture"])
    manual = _strict_workflow((ROOT / ".github/workflows/manual-perf.yml").read_text(encoding="utf-8"))
    manual_run = next(
        step["run"]
        for step in manual["jobs"]["scale"]["steps"]
        if step.get("name") == "Run explicit large-count descriptors"
    )
    assert _inventory_matches(_collect_nodes(_fixed_test_paths(manual_run)), manifest["lanes"]["manual_perf"])

    unit314 = workflow["jobs"]["unit_test_py314"]["strategy"]["matrix"]["include"][0]["args"].split()
    expected = manifest["lanes"]["unit"] + manifest["lanes"]["architecture"]
    expected += [node for node in manifest["lanes"]["nightly"] if node.split("::")[0] in unit314]
    assert _inventory_matches(_collect_nodes(unit314), expected)
    integration314 = next(
        step["run"]
        for step in workflow["jobs"]["integration_test_py314"]["steps"]
        if step.get("name") == "Run authoring and MCP integration tests"
    )
    integration_paths = _fixed_test_paths(integration314)
    expected = [
        node
        for node in manifest["lanes"]["integration"]
        if node.startswith(("tests_ce/integration_tests/test_authoring/", "tests_ce/integration_tests/test_mcp/"))
    ]
    expected += [node for node in manifest["lanes"]["nightly"] if node.split("::")[0] in integration_paths]
    assert _inventory_matches(_collect_nodes(integration_paths), expected)
    all_nodes = set().union(*map(set, manifest["lanes"].values()))
    for job_name in ("windows_pr_tests", "runtime_determinism_matrix"):
        for step in workflow["jobs"][job_name]["steps"]:
            command = step.get("run", "")
            if "uv run pytest" not in command:
                continue
            selected = _collect_nodes(_fixed_test_paths(command))
            assert len(selected) == len(set(selected)) and set(selected) <= all_nodes, step["name"]


def _function_hash(tree, name):
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(functions) != 1:
        raise ValueError(f"expected exactly one function {name!r}, found {len(functions)}")
    function = copy.deepcopy(functions[0])
    for node in ast.walk(function):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and getattr(node, "type_params", None) == []:
            node._fields = tuple(field for field in node._fields if field != "type_params")
    # Python 3.14 changed ast.dump's default to hide empty lists; retain the 3.11 representation.
    options = {"show_empty": True} if sys.version_info >= (3, 14) else {}
    return hashlib.sha256(ast.dump(function, include_attributes=False, **options).encode("utf-8")).hexdigest()


def _parent_path(path):
    return (
        path.replace("tests_ce/integration_tests/test_authoring/", "tests_ce/unit_tests/test_authoring/", 1)
        .replace("tests_ce/nightly_tests/test_authoring/", "tests_ce/unit_tests/test_authoring/", 1)
        .replace("tests_ce/nightly_tests/test_benchmarks/", "tests_ce/unit_tests/test_benchmarks/", 1)
    )


def _baseline_source(parent, manifest, baseline_dir):
    path = baseline_dir / (Path(parent).name + ".txt")
    try:
        source = path.read_bytes()
    except FileNotFoundError as error:
        raise AssertionError(f"missing baseline fixture: {path}") from error
    expected = manifest["baseline_sha256"][parent]
    assert hashlib.sha256(source).hexdigest() == expected, f"baseline fixture SHA-256 mismatch: {path}"
    return source.decode("utf-8")


def _moved_hashes(nodes, manifest, baseline_dir=ROOT / "tests_ce/fixtures/lane_baseline"):
    current_trees = {}
    parent_trees = {}
    current_hashes = {}
    parent_hashes = {}
    for node in nodes:
        path, name = node.split("::", 1)
        name = name.split("[", 1)[0]
        parent = _parent_path(path)
        if path not in current_trees:
            current_trees[path] = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        if parent not in parent_trees:
            source = _baseline_source(parent, manifest, baseline_dir)
            parent_trees[parent] = ast.parse(source)
        current_hashes[node] = _function_hash(current_trees[path], name)
        parent_hashes[node] = _function_hash(parent_trees[parent], name)
    return current_hashes, parent_hashes


def _moved_hashes_match(nodes, manifest, current, parent):
    hashes = manifest["moved_ast_hashes"]
    exceptions = manifest["moved_ast_hash_exceptions"]
    exceptional = {entry["node_id"]: entry for entry in exceptions}
    if len(nodes) != 279 or len(set(nodes)) != 279 or len(hashes) != 268 or len(exceptions) != len(exceptional):
        return False
    if len(exceptions) != 11 or set(hashes) & set(exceptional) or set(hashes) | set(exceptional) != set(nodes):
        return False
    for node in nodes:
        if node in exceptional:
            entry = exceptional[node]
            if not entry["reason"] or entry["current_hash"] != current[node] or entry["parent_hash"] != parent[node]:
                return False
        elif hashes[node] != current[node] or hashes[node] != parent[node]:
            return False
    return True


def test_lane_manifest_and_parent_function_hashes(tmp_path):
    manifest = json.loads((ROOT / "tests_ce/fixtures/lane_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_commit"] == "a2954317"
    assert set(manifest["lanes"]) == set(LANES)
    for lane, paths in LANES.items():
        nodes = _collect_nodes(paths)
        assert _inventory_matches(nodes, manifest["lanes"][lane]), lane
        if lane == "precommit":
            assert len(nodes) == 168
            assert _inventory_matches(nodes, manifest["precommit_exact"])
            assert not _inventory_matches(nodes, manifest["precommit_exact"][:-1])
            assert not _inventory_matches(nodes, manifest["precommit_exact"][:-1] + ["different-node"])
            assert not _inventory_matches(nodes, manifest["precommit_exact"][:-1] + [manifest["precommit_exact"][0]])

    moved_paths = [
        "tests_ce/integration_tests/test_authoring/test_bounded_executor.py",
        "tests_ce/integration_tests/test_authoring/test_bounded_python_library.py",
        "tests_ce/integration_tests/test_authoring/test_build_verification.py",
        "tests_ce/integration_tests/test_authoring/test_set_order_scan.py",
        "tests_ce/nightly_tests/test_authoring/test_build_verification.py",
        "tests_ce/nightly_tests/test_benchmarks",
    ]
    nodes = _collect_nodes(moved_paths)
    assert set(manifest["baseline_sha256"]) == {_parent_path(node.split("::", 1)[0]) for node in nodes}
    current, parent = _moved_hashes(nodes, manifest)
    assert _moved_hashes_match(nodes, manifest, current, parent)
    baseline_parent = next(iter(manifest["baseline_sha256"]))
    fixture = tmp_path / (Path(baseline_parent).name + ".txt")
    fixture.write_bytes((ROOT / "tests_ce/fixtures/lane_baseline" / fixture.name).read_bytes() + b"\n# mutant\n")
    with pytest.raises(AssertionError, match="baseline fixture SHA-256 mismatch"):
        _baseline_source(baseline_parent, manifest, tmp_path)
    fixture.unlink()
    with pytest.raises(AssertionError, match="missing baseline fixture"):
        _baseline_source(baseline_parent, manifest, tmp_path)
    mutant_current = current.copy()
    first = next(iter(manifest["moved_ast_hashes"]))
    path, name = first.split("::", 1)
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name.split("[", 1)[0])
    function.body.append(ast.Pass())
    mutant_current[first] = _function_hash(tree, function.name)
    assert not _moved_hashes_match(nodes, manifest, mutant_current, parent)
    exception_node = manifest["moved_ast_hash_exceptions"][0]["node_id"]
    path, name = exception_node.split("::", 1)
    name = name.split("[", 1)[0]
    original_tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for mutation in ("helper", "assertion", "nonempty_type_params"):
        tree = copy.deepcopy(original_tree)
        function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
        if mutation == "helper":
            call = next(n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name))
            call.func.id += "_mutant"
        elif mutation == "assertion":
            assertion = next(n for n in ast.walk(function) if isinstance(n, ast.Assert))
            assertion.test = ast.Constant(value=True)
        else:
            function._fields = (*[field for field in function._fields if field != "type_params"], "type_params")
            function.type_params = [ast.Name(id="T", ctx=ast.Load())]
        mutant_current = current.copy()
        mutant_current[exception_node] = _function_hash(tree, name)
        assert not _moved_hashes_match(nodes, manifest, mutant_current, parent), mutation
    empty_tree = copy.deepcopy(original_tree)
    empty_function = next(n for n in ast.walk(empty_tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    empty_function._fields = (*[field for field in empty_function._fields if field != "type_params"], "type_params")
    empty_function.type_params = []
    assert _function_hash(empty_tree, name) == current[exception_node]
    exception = manifest["moved_ast_hash_exceptions"][0]
    for field in ("current_hash", "parent_hash"):
        original = exception[field]
        exception[field] = "0" * 64
        assert not _moved_hashes_match(nodes, manifest, current, parent)
        exception[field] = original


def test_platform_node_selection_exceptions_are_exact():
    workflow = yaml.safe_load((ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8"))
    steps = [
        *workflow["jobs"]["windows_pr_tests"]["steps"],
        *workflow["jobs"]["architecture_tests"]["steps"],
    ]
    selected = set()
    for step in steps:
        if step.get("name") in (
            "Run Windows portability and authoring proofs",
            "Run seeded DSL replay and negative control",
        ):
            selected.update(re.findall(r"(tests_ce/[^\s'\"]+?\.py)::", step.get("run", "")))
    assert selected == ALLOWED_PLATFORM_NODE_SELECTIONS


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
