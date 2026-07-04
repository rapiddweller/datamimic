#!/usr/bin/env python
"""Prompt-variant benchmark for local models authoring DATAMIMIC DSL.

Matrix: MODELS x PROMPT_VARIANTS x TASKS, driven through the local Ollama chat
API. Each generation is scored with the repo's own authoring APIs
(datamimic_ce.authoring: lint_source, dry_run_source) plus a per-task intent
check against the dry-run sample rows.

Usage: see README.md in this directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from datamimic_ce.authoring import lint_source
from datamimic_ce.authoring.diagnostics import Severity
from datamimic_ce.authoring.dryrun import DryRunResult, dry_run_source
from datamimic_ce.authoring.reference import load_recipe, reference

OLLAMA_URL = "http://localhost:11434/api/chat"
TEMPERATURE = 0.2
NUM_PREDICT = 1400
NUM_CTX = 8192  # P2/P3 prompts run well past Ollama's default 2048/4096 context
CALL_TIMEOUT_S = 300
DRY_RUN_TIMEOUT_S = 45
SAMPLE_ROWS = 60
MAX_COUNT = 60

RESULTS_DIR = Path(__file__).parent / "results"

DEFAULT_MODELS = ["qwen2.5:7b", "gemma4:31b"]  # fast model first


# --------------------------------------------------------------------------- #
# Generic helpers over DryRunResult sample rows (field names are not
# controlled by us -- the model picks them -- so every intent check matches on
# case-insensitive substrings rather than exact keys).
# --------------------------------------------------------------------------- #


def find_key(row: dict[str, Any], *substrings: str) -> str | None:
    """First key (by priority of `substrings`, then insertion order) containing
    the substring, case-insensitively. None if nothing matches."""
    for sub in substrings:
        for k in row:
            if sub in k.lower():
                return k
    return None


def walk_values(obj: Any):
    """Yield obj and every value nested inside it (dicts/lists), depth-first."""
    yield obj
    if isinstance(obj, dict):
        for v in obj.values():
            yield from walk_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_values(v)


def all_rows(result: DryRunResult):
    for p in result.products:
        yield from p.sample


def products_with_keys(products: list, *substrings: str) -> list:
    """Products whose sample rows collectively expose keys matching every
    substring (used to pair up e.g. a 'branches' and a 'customers' product)."""
    matches = []
    for p in products:
        if not p.sample:
            continue
        keys = set()
        for row in p.sample:
            keys.update(k.lower() for k in row)
        if all(any(sub in k for k in keys) for sub in substrings):
            matches.append(p)
    return matches


def _norm(v: Any) -> str:
    return str(v)


# --------------------------------------------------------------------------- #
# Intent checks -- one per task id. Signature: (xml: str, result: DryRunResult) -> bool
# --------------------------------------------------------------------------- #


def check_weighted_country(xml: str, result: DryRunResult) -> bool:
    countries: set[str] = set()
    has_space_name = False
    for row in all_rows(result):
        for k, v in row.items():
            lk = k.lower()
            if "country" in lk and isinstance(v, str):
                countries.add(v)
            if "name" in lk and isinstance(v, str) and " " in v.strip():
                has_space_name = True
    if not countries:
        return False
    if not countries.issubset({"US", "DE", "VN"}):
        return False
    return has_space_name


def check_nested_reviews(xml: str, result: DryRunResult) -> bool:
    for row in all_rows(result):
        for val in walk_values(row):
            if not isinstance(val, list):
                continue
            for el in val:
                if not isinstance(el, dict):
                    continue
                rk = find_key(el, "rating")
                if rk is None:
                    continue
                rv = el[rk]
                if isinstance(rv, bool):
                    continue
                if isinstance(rv, int) and 1 <= rv <= 5:
                    return True
    return False


def check_reproducible_orders(xml: str, result: DryRunResult) -> bool:
    result2 = dry_run_source(xml, max_count=MAX_COUNT, sample_rows=SAMPLE_ROWS, timeout_seconds=DRY_RUN_TIMEOUT_S)
    if not result2.ok:
        return False
    p1 = {p.name: p.sample for p in result.products}
    p2 = {p.name: p.sample for p in result2.products}
    if set(p1) != set(p2):
        return False
    for name in p1:
        if p1[name] != p2[name]:
            return False
    statuses: set[Any] = set()
    for row in all_rows(result):
        k = find_key(row, "status")
        if k is not None:
            statuses.add(row[k])
    if not statuses:
        return False
    return statuses.issubset({"new", "paid", "shipped"})


def check_memstore_pipeline(xml: str, result: DryRunResult) -> bool:
    for p in result.products:
        checked = 0
        ok = True
        for row in p.sample:
            dk = find_key(row, "doubled")
            vk = find_key(row, "value")
            if dk is None or vk is None or dk == vk:
                continue
            dv, vv = row[dk], row[vk]
            if not isinstance(dv, int | float) or not isinstance(vv, int | float):
                continue
            checked += 1
            if dv != 2 * vv:
                ok = False
                break
        if checked > 0 and ok:
            return True
    return False


def check_timeseries(xml: str, result: DryRunResult) -> bool:
    total = sum(p.count for p in result.products)
    if total != 48:
        return False
    hours: set[Any] = set()
    sensors: set[Any] = set()
    for row in all_rows(result):
        hk = find_key(row, "hour")
        sk = find_key(row, "sensor")
        if hk is not None:
            hours.add(row[hk])
        if sk is not None:
            sensors.add(row[sk])
    return 23 in hours and len(sensors) == 2


def _check_branch_fk_nested(products: list) -> bool | None:
    """Embedded shape: a branch row carries branch_id/city AND a nested list of
    customer dicts that repeat those same values. Returns None if no such shape
    is present in the sample (caller falls back to the flat-product check)."""
    found_any = False
    for p in products:
        for row in p.sample:
            row_bid_key = find_key(row, "branch_id", "branchid")
            row_city_key = find_key(row, "city")
            if row_bid_key is None or row_city_key is None:
                continue
            for v in row.values():
                if not isinstance(v, list):
                    continue
                children = [el for el in v if isinstance(el, dict)]
                relevant = [
                    el for el in children if find_key(el, "branch_id", "branchid") and find_key(el, "city")
                ]
                if not relevant:
                    continue
                found_any = True
                for child in relevant:
                    cbid_key = find_key(child, "branch_id", "branchid")
                    ccity_key = find_key(child, "city")
                    if child.get(cbid_key) != row.get(row_bid_key):
                        return False
                    if child.get(ccity_key) != row.get(row_city_key):
                        return False
    return True if found_any else None


def _check_branch_fk_flat(products: list) -> bool:
    """Two-product shape: a 'branches' product and a 'customers' product joined
    on branch_id, each carrying its own city."""
    candidates = products_with_keys(products, "city")
    branch_like = [p for p in candidates if any("branch" in k for row in p.sample for k in row)]
    if len(branch_like) < 2:
        return False
    branch_like = sorted(branch_like, key=lambda p: p.count)
    branches, customers = branch_like[0], branch_like[-1]
    if not branches.sample or not customers.sample:
        return False
    b_id_key = find_key(branches.sample[0], "branch_id", "branchid", "id")
    b_city_key = find_key(branches.sample[0], "city")
    if b_id_key is None or b_city_key is None:
        return False
    branch_map = {_norm(row.get(b_id_key)): row.get(b_city_key) for row in branches.sample}
    c_id_key = find_key(customers.sample[0], "branch_id", "branchid")
    c_city_key = find_key(customers.sample[0], "city")
    if c_id_key is None or c_city_key is None:
        return False
    matched_any = False
    for row in customers.sample:
        bid = _norm(row.get(c_id_key))
        if bid not in branch_map:
            return False
        matched_any = True
        if row.get(c_city_key) != branch_map[bid]:
            return False
    return matched_any


def check_branch_fk(xml: str, result: DryRunResult) -> bool:
    products = [p for p in result.products if p.sample]
    nested = _check_branch_fk_nested(products)
    if nested is not None:
        return nested
    return _check_branch_fk_flat(products)


# --------------------------------------------------------------------------- #
# The shared task set (ids are fixed -- a Haiku track run by the controller
# uses the same set).
# --------------------------------------------------------------------------- #

TASKS: list[dict[str, Any]] = [
    {
        "id": "weighted_country",
        "prompt": (
            "50 customers: an incrementing id, a real person full name, an age between 18 and 90, "
            "and a country from the fixed list US, DE, VN weighted 0.5/0.3/0.2. Export JSON."
        ),
        "intent_check": check_weighted_country,
    },
    {
        "id": "nested_reviews",
        "prompt": (
            "20 products: a SKU code (pattern), a decimal price, and a nested list of 1-3 reviews, "
            "each with an integer rating 1-5. JSON."
        ),
        "intent_check": check_nested_reviews,
    },
    {
        "id": "reproducible_orders",
        "prompt": (
            "A reproducible run of 30 orders: order_id increments, status one of new/paid/shipped, "
            "total is a decimal. Same output every run. JSON."
        ),
        "intent_check": check_reproducible_orders,
    },
    {
        "id": "memstore_pipeline",
        "prompt": (
            "Generate 15 rows (id, value int 1-100) into a memstore, then a second generate reads "
            "them back in order and adds doubled = value*2. JSON."
        ),
        "intent_check": check_memstore_pipeline,
    },
    {
        "id": "timeseries",
        "prompt": (
            "Hourly sensor readings across one day for 2 sensors: timestamp, hour index, sensor "
            "number, temperature. JSON."
        ),
        "intent_check": check_timeseries,
    },
    {
        "id": "branch_fk",
        "prompt": (
            "10 branches (branch_id, city) and 2-4 customers per branch, each customer carrying "
            "its branch's real branch_id and city. JSON."
        ),
        "intent_check": check_branch_fk,
    },
]

TASKS_BY_ID = {t["id"]: t for t in TASKS}


# --------------------------------------------------------------------------- #
# Prompt variants -- the benchmark axis.
# --------------------------------------------------------------------------- #


def _p0(task_prompt: str) -> str:
    return f"Write a DATAMIMIC XML descriptor (<setup> root) for this task. Output ONLY the XML.\nTask: {task_prompt}"


_INTENT_TABLE = """
Value-source mapping -- pick the one matching the field's meaning:
- fixed set of options -> values="'a','b'" (+ weights="0.x,0.y")
- number range -> type="int|decimal" min=... max=...
- real person name/email -> <variable name="p" entity="Person"/> then script="p.name" \
(inside nested scopes use this.p.name)
- unique id -> generator="IncrementGenerator"
- coded string -> pattern="[A-Z]{3}-[0-9]{4}"
- list of sub-records -> <nestedKey type="list" minCount=... maxCount=...> with child <key>s
- computed value -> script=... (python; earlier sibling keys via this.field)
- reproducible run -> <setup rngSeed="1">
- memstore pipeline -> <memstore id="m"/> + target="m,JSON" then \
<generate source="m" type="<name>" distribution="ordered">
- time-series -> <generate start="..." end="..." interval="PT1H" count="<series>"> with \
script="ts.now"/"ts.step"/"ts.series"
- parent/child -> nest <generate> inside <generate>, child reads parent.field
""".strip()


def _p1(task_prompt: str) -> str:
    return f"{_p0(task_prompt)}\n\n{_INTENT_TABLE}"


def _p2(task_prompt: str) -> str:
    return f"{_p0(task_prompt)}\n\n{reference('overview')}"


def _p3(task_prompt: str) -> str:
    example = load_recipe("relational-parent-child")
    return f"{_p0(task_prompt)}\n\nHere is a valid example descriptor:\n\n{example}"


PROMPT_VARIANTS: dict[str, Callable[[str], str]] = {
    "P0_bare": _p0,
    "P1_intent_table": _p1,
    "P2_cheatsheet": _p2,
    "P3_fewshot": _p3,
}


# --------------------------------------------------------------------------- #
# Ollama call
# --------------------------------------------------------------------------- #


class OllamaTimeout(Exception):
    pass


def call_ollama(model: str, prompt: str, *, timeout: int = CALL_TIMEOUT_S) -> tuple[str | None, int, str | None]:
    """Returns (content, latency_ms, error). error is None on success."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,  # verified harmless on non-thinking models; required for gemma4:31b
        "options": {"temperature": TEMPERATURE, "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        latency_ms = int((time.perf_counter() - started) * 1000)
        content = data.get("message", {}).get("content", "")
        return content, latency_ms, None
    except TimeoutError:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return None, latency_ms, "timeout"
    except (urllib.error.URLError, OSError) as err:
        latency_ms = int((time.perf_counter() - started) * 1000)
        is_timeout = isinstance(err, TimeoutError) or "timed out" in str(err).lower()
        return None, latency_ms, "timeout" if is_timeout else str(err)
    except Exception as err:  # malformed JSON, etc.
        latency_ms = int((time.perf_counter() - started) * 1000)
        return None, latency_ms, str(err)


# --------------------------------------------------------------------------- #
# Extraction + scoring
# --------------------------------------------------------------------------- #

_SETUP_START_RE = re.compile(r"<setup\b", re.IGNORECASE)


def extract_setup(text: str) -> str | None:
    """First <setup ...>...</setup> block. Models may wrap the XML in markdown
    fences; the regex only anchors on the tag itself so fences are irrelevant.
    If the reply was cut off mid-descriptor, close the tag rather than discard."""
    m = _SETUP_START_RE.search(text)
    if not m:
        return None
    frag = text[m.start() :]
    end = frag.lower().find("</setup>")
    if end != -1:
        return frag[: end + len("</setup>")]
    return frag.rstrip() + "\n</setup>"


def score_generation(task: dict[str, Any], raw_reply: str) -> dict[str, Any]:
    xml = extract_setup(raw_reply)
    if xml is None:
        return {"score": 0, "rule_ids": ["NO_XML"], "detail": "no <setup> block found in reply"}

    lint = lint_source(xml)
    if not lint.ok:
        rule_ids = sorted({d.rule for d in lint.diagnostics if d.severity == Severity.ERROR})
        return {"score": 0, "rule_ids": rule_ids, "detail": f"lint: {lint.summary()}"}

    try:
        result = dry_run_source(xml, max_count=MAX_COUNT, sample_rows=SAMPLE_ROWS, timeout_seconds=DRY_RUN_TIMEOUT_S)
    except Exception as err:
        return {"score": 0, "rule_ids": ["EXCEPTION"], "detail": f"dry_run_source raised: {err}"}

    total_rows = sum(p.count for p in result.products)
    if not result.ok or total_rows == 0:
        rule_ids = sorted({d.rule for d in result.diagnostics}) or ["DM000"]
        return {"score": 0, "rule_ids": rule_ids, "detail": "dry-run failed or produced 0 rows"}

    try:
        intent_ok = bool(task["intent_check"](xml, result))
    except Exception as err:
        return {"score": 1, "rule_ids": [], "detail": f"intent check raised: {err}"}

    if intent_ok:
        return {"score": 2, "rule_ids": [], "detail": "intent check passed"}
    return {"score": 1, "rule_ids": [], "detail": "runs but intent check failed"}


# --------------------------------------------------------------------------- #
# Golden-descriptor self-test (no Ollama involved) -- run before burning GPU
# time on the real matrix, to de-risk the scoring layer itself.
# --------------------------------------------------------------------------- #

GOLDEN_DESCRIPTORS: dict[str, str] = {
    "weighted_country": """
<setup rngSeed="1">
  <generate name="customers" count="50" target="JSON">
    <key name="id" generator="IncrementGenerator"/>
    <variable name="p" entity="Person" dataset="US" locale="en"/>
    <key name="full_name" script="p.name"/>
    <key name="age" type="int" min="18" max="90"/>
    <key name="country" values="'US','DE','VN'" weights="0.5,0.3,0.2"/>
  </generate>
</setup>
""",
    "nested_reviews": """
<setup rngSeed="1">
  <generate name="products" count="20" target="JSON">
    <key name="sku" pattern="[A-Z]{3}-[0-9]{4}"/>
    <key name="price" type="decimal" min="1" max="500"/>
    <nestedKey name="reviews" type="list" minCount="1" maxCount="3">
      <key name="rating" type="int" min="1" max="5"/>
    </nestedKey>
  </generate>
</setup>
""",
    "reproducible_orders": """
<setup rngSeed="1">
  <generate name="orders" count="30" target="JSON">
    <key name="order_id" generator="IncrementGenerator"/>
    <key name="status" values="'new','paid','shipped'"/>
    <key name="total" type="decimal" min="1" max="500"/>
  </generate>
</setup>
""",
    "memstore_pipeline": """
<setup rngSeed="1">
  <memstore id="m"/>
  <generate name="rows" count="15" target="m,JSON">
    <key name="id" generator="IncrementGenerator"/>
    <key name="value" type="int" min="1" max="100"/>
  </generate>
  <generate name="doubled_rows" source="m" type="rows" distribution="ordered" target="JSON">
    <key name="id" script="id"/>
    <key name="value" script="value"/>
    <key name="doubled" script="value * 2"/>
  </generate>
</setup>
""",
    "timeseries": """
<setup rngSeed="1">
  <generate name="readings" start="2025-01-01T00:00:00" end="2025-01-02T00:00:00" interval="PT1H"
            count="2" target="JSON">
    <key name="timestamp" script="ts.now"/>
    <key name="hour_index" script="ts.step"/>
    <key name="sensor_number" script="ts.series"/>
    <key name="temperature" type="decimal" min="15" max="28"/>
  </generate>
</setup>
""",
    "branch_fk_flat": """
<setup rngSeed="1">
  <memstore id="mem"/>
  <generate name="branches" count="10" target="mem,JSON">
    <key name="branch_id" generator="IncrementGenerator"/>
    <key name="city" values="'Berlin','Hanoi','Austin','Paris'"/>
    <generate name="customers" minCount="2" maxCount="4" target="mem,JSON">
      <key name="customer_id" generator="IncrementGenerator"/>
      <key name="branch_id" script="parent.branch_id"/>
      <key name="city" script="parent.city"/>
    </generate>
  </generate>
</setup>
""",
    "branch_fk_nested": """
<setup rngSeed="1">
  <generate name="branches" count="10" target="JSON">
    <key name="branch_id" generator="IncrementGenerator"/>
    <key name="city" values="'Berlin','Hanoi','Austin','Paris'"/>
    <nestedKey name="customers" type="list" minCount="2" maxCount="4">
      <key name="customer_id" generator="IncrementGenerator"/>
      <key name="branch_id" script="parent.branch_id"/>
      <key name="city" script="parent.city"/>
    </nestedKey>
  </generate>
</setup>
""",
}


def run_selftest() -> bool:
    all_ok = True
    for key, xml in GOLDEN_DESCRIPTORS.items():
        task_id = key.split("_flat")[0].split("_nested")[0] if key.startswith("branch_fk") else key
        task = TASKS_BY_ID[task_id]
        result = score_generation(task, xml)
        status = "OK" if result["score"] == 2 else "FAIL"
        if result["score"] != 2:
            all_ok = False
        print(f"[{status}] {key}: score={result['score']} detail={result['detail']}")
    return all_ok


# --------------------------------------------------------------------------- #
# Matrix runner
# --------------------------------------------------------------------------- #


def run_matrix(
    models: list[str],
    variants: list[str],
    tasks: list[dict[str, Any]],
    *,
    out_path: Path,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    def persist() -> None:
        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "models": models,
            "variants": variants,
            "tasks": [t["id"] for t in tasks],
            "cells": cells,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for model in models:
        consecutive_timeouts = 0
        skip_rest = False
        for variant in variants:
            for task in tasks:
                cell: dict[str, Any] = {"model": model, "variant": variant, "task": task["id"]}
                if skip_rest:
                    cell.update(score="timeout", rule_ids=[], latency_ms=None, detail="skipped: 2 consecutive timeouts")
                    cells.append(cell)
                    persist()
                    continue

                prompt = PROMPT_VARIANTS[variant](task["prompt"])
                print(f"-> {model} / {variant} / {task['id']}", file=sys.stderr, flush=True)
                content, latency_ms, err = call_ollama(model, prompt)

                if err is not None:
                    is_timeout = err == "timeout"
                    consecutive_timeouts = consecutive_timeouts + 1 if is_timeout else 0
                    cell.update(
                        score="timeout" if is_timeout else "error",
                        rule_ids=[],
                        latency_ms=latency_ms,
                        detail=err,
                    )
                    cells.append(cell)
                    persist()
                    if consecutive_timeouts >= 2:
                        print(f"   {model}: 2 consecutive timeouts, skipping remaining cells", file=sys.stderr)
                        skip_rest = True
                    continue

                consecutive_timeouts = 0
                result = score_generation(task, content or "")
                cell.update(result, latency_ms=latency_ms)
                cells.append(cell)
                print(f"   score={result['score']} ({latency_ms} ms)", file=sys.stderr)
                persist()

    return cells


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def _fmt_score(score: Any) -> str:
    return str(score)


def render_report(
    cells: list[dict[str, Any]], models: list[str], variants: list[str], tasks: list[dict[str, Any]]
) -> str:
    lines: list[str] = []
    for model in models:
        model_cells = [c for c in cells if c["model"] == model]
        if not model_cells:
            continue
        lines.append(f"## {model}")
        lines.append("")
        header = "| task | " + " | ".join(variants) + " |"
        sep = "|---" * (len(variants) + 1) + "|"
        lines.append(header)
        lines.append(sep)
        by_key = {(c["variant"], c["task"]): c for c in model_cells}
        for task in tasks:
            row = [task["id"]]
            for variant in variants:
                c = by_key.get((variant, task["id"]))
                row.append(_fmt_score(c["score"]) if c else "-")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        totals = []
        for variant in variants:
            vcells = [c for c in model_cells if c["variant"] == variant]
            intent_correct = sum(1 for c in vcells if c["score"] == 2)
            runs = sum(1 for c in vcells if c["score"] in (1, 2))
            totals.append(f"{variant}: intent-correct {intent_correct}/{len(tasks)}, runs {runs}/{len(tasks)}")
        lines.append(" | ".join(totals))
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--selftest", action="store_true", help="validate intent checks against golden descriptors, no Ollama calls"
    )
    parser.add_argument(
        "--smoke", action="store_true", help="run a single cell: gemma4:31b / P1_intent_table / weighted_country"
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--variants", nargs="+", default=list(PROMPT_VARIANTS))
    parser.add_argument("--tasks", nargs="+", default=[t["id"] for t in TASKS])
    parser.add_argument("--out", default=None, help="results json path (default: results/<timestamp>.json)")
    args = parser.parse_args()

    if args.selftest:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"{timestamp}.json"

    if args.smoke:
        models, variants, tasks = ["gemma4:31b"], ["P1_intent_table"], [TASKS_BY_ID["weighted_country"]]
    else:
        models = args.models
        variants = args.variants
        tasks = [TASKS_BY_ID[t] for t in args.tasks]

    cells = run_matrix(models, variants, tasks, out_path=out_path)
    report = render_report(cells, models, variants, tasks)
    print(report)
    (RESULTS_DIR / "latest.md").write_text(report, encoding="utf-8")
    print(f"\nresults json: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
