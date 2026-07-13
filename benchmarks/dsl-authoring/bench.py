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
NUM_CTX_LOOP = 16384  # loop keeps the cheatsheet + up to LOOP_MAX_ITERATIONS replies + feedback in
# context -- each reply is embedded twice (assistant turn + re-quoted in the next feedback
# message), so watch for silent truncation of the cheatsheet on later iterations if this or
# LOOP_MAX_ITERATIONS grows further (call_ollama discards Ollama's prompt_eval_count, which
# would otherwise flag it).
CALL_TIMEOUT_S = 300
LOOP_MAX_ITERATIONS = 6
LOOP_VARIANT = "loop"
DRY_RUN_TIMEOUT_S = 45
SAMPLE_ROWS = 60
MAX_COUNT = 60

RESULTS_DIR = Path(__file__).parent / "results"

DEFAULT_MODELS = ["gemma4:12b", "gemma4:31b"]  # fast model first; see README "Local model selection"


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
        "intent_text": (
            "every country value must be one of US, DE, VN (none outside that set) and a name "
            "field must contain a real full name with a space in it"
        ),
    },
    {
        "id": "nested_reviews",
        "prompt": (
            "20 products: a SKU code (pattern), a decimal price, and a nested list of 1-3 reviews, "
            "each with an integer rating 1-5. JSON."
        ),
        "intent_check": check_nested_reviews,
        "intent_text": (
            "some field must be a real list of review objects (a JSON array of dicts), each "
            "containing an integer rating between 1 and 5"
        ),
    },
    {
        "id": "reproducible_orders",
        "prompt": (
            "A reproducible run of 30 orders: order_id increments, status one of new/paid/shipped, "
            "total is a decimal. Same output every run. JSON."
        ),
        "intent_check": check_reproducible_orders,
        "intent_text": (
            "two runs must produce identical rows (seed the run with <setup rngSeed=...>) and "
            "every status value must be exactly one of: new, paid, shipped"
        ),
    },
    {
        "id": "memstore_pipeline",
        "prompt": (
            "Generate 15 rows (id, value int 1-100) into a memstore, then a second generate reads "
            "them back in order and adds doubled = value*2. JSON."
        ),
        "intent_check": check_memstore_pipeline,
        "intent_text": (
            "the second product must carry both the original value and a doubled field where "
            "doubled == 2 * value on every row"
        ),
    },
    {
        "id": "timeseries",
        "prompt": (
            "Hourly sensor readings across one day for 2 sensors: timestamp, hour index, sensor "
            "number, temperature. JSON."
        ),
        "intent_check": check_timeseries,
        "intent_text": (
            "exactly 48 rows total (24 hours x 2 sensors), an hour index field reaching 23, and "
            "exactly two distinct sensor numbers"
        ),
    },
    {
        "id": "branch_fk",
        "prompt": (
            "10 branches (branch_id, city) and 2-4 customers per branch, each customer carrying "
            "its branch's real branch_id and city. JSON."
        ),
        "intent_check": check_branch_fk,
        "intent_text": (
            "every customer must carry the branch_id AND the city of its own branch (the "
            "customer's city equal to its branch's city, joined on branch_id)"
        ),
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


def call_ollama(
    model: str,
    prompt: str | list[dict[str, str]],
    *,
    timeout: int = CALL_TIMEOUT_S,
    num_ctx: int = NUM_CTX,
) -> tuple[str | None, int, str | None]:
    """Returns (content, latency_ms, error). error is None on success.
    `prompt` is a single user message or a full chat message list (loop mode)."""
    messages = [{"role": "user", "content": prompt}] if isinstance(prompt, str) else prompt
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,  # verified harmless on non-thinking models; required for gemma4:31b
        "options": {"temperature": TEMPERATURE, "num_predict": NUM_PREDICT, "num_ctx": num_ctx},
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


_MAX_FEEDBACK_DIAGS = 12


def _diag_lines(diagnostics: list) -> str:
    """Compact `- [rule] message | fix: hint` block, capped to bound tokens."""
    lines = [f"- [{d.rule}] {d.message} | fix: {d.fix_hint}" for d in diagnostics[:_MAX_FEEDBACK_DIAGS]]
    dropped = len(diagnostics) - _MAX_FEEDBACK_DIAGS
    if dropped > 0:
        lines.append(f"- ... and {dropped} more findings of the same kinds")
    return "\n".join(lines)


def _feedback(problem_block: str, xml: str | None) -> str:
    parts = [problem_block]
    if xml is not None:
        parts.append(f"Your previous descriptor:\n{xml}")
    parts.append("Return a corrected COMPLETE descriptor (<setup> root). Output ONLY the XML.")
    return "\n\n".join(parts)


def evaluate_generation(task: dict[str, Any], raw_reply: str) -> dict[str, Any]:
    """Score one generation and, when it is not intent-correct, build the feedback
    message the loop condition sends back to the model. Keys: score, rule_ids,
    detail, feedback (None when score is 2)."""
    xml = extract_setup(raw_reply)
    if xml is None:
        return {
            "score": 0,
            "rule_ids": ["NO_XML"],
            "detail": "no <setup> block found in reply",
            "feedback": _feedback("No <setup> descriptor block was found in your reply.", None),
        }

    lint = lint_source(xml)
    if not lint.ok:
        errors = [d for d in lint.diagnostics if d.severity == Severity.ERROR]
        rule_ids = sorted({d.rule for d in errors})
        return {
            "score": 0,
            "rule_ids": rule_ids,
            "detail": f"lint: {lint.summary()}",
            "feedback": _feedback(f"The descriptor has lint errors:\n{_diag_lines(errors)}", xml),
        }

    try:
        result = dry_run_source(xml, max_count=MAX_COUNT, sample_rows=SAMPLE_ROWS, timeout_seconds=DRY_RUN_TIMEOUT_S)
    except Exception as err:
        return {
            "score": 0,
            "rule_ids": ["EXCEPTION"],
            "detail": f"dry_run_source raised: {err}",
            "feedback": _feedback(f"Executing the descriptor failed: {err}", xml),
        }

    total_rows = sum(p.count for p in result.products)
    if not result.ok or total_rows == 0:
        rule_ids = sorted({d.rule for d in result.diagnostics}) or ["DM000"]
        return {
            "score": 0,
            "rule_ids": rule_ids,
            "detail": "dry-run failed or produced 0 rows",
            "feedback": _feedback(
                f"The descriptor runs into errors (a test run produced no usable data):\n"
                f"{_diag_lines(result.diagnostics)}",
                xml,
            ),
        }

    try:
        intent_ok = bool(task["intent_check"](xml, result))
    except Exception as err:
        return {"score": 1, "rule_ids": [], "detail": f"intent check raised: {err}", "feedback": None}

    if intent_ok:
        return {"score": 2, "rule_ids": [], "detail": "intent check passed", "feedback": None}

    first_row: dict[str, Any] | None = next(iter(all_rows(result)), None)
    row_note = f"\nFirst generated row: {json.dumps(first_row, default=str)[:400]}" if first_row else ""
    return {
        "score": 1,
        "rule_ids": [],
        "detail": "runs but intent check failed",
        "feedback": _feedback(
            f"The descriptor runs, but the output does not satisfy: {task['intent_text']}.{row_note}",
            xml,
        ),
    }


def score_generation(task: dict[str, Any], raw_reply: str) -> dict[str, Any]:
    info = evaluate_generation(task, raw_reply)
    return {k: info[k] for k in ("score", "rule_ids", "detail")}


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

    # best-of-N must survive a later regression (the bug this replaced: reporting the LAST
    # iteration even when an earlier one scored higher) and break ties toward fewer errors,
    # then the earliest iteration (fastest convergence).
    cases = [
        ([0, 1, 0], 1),  # regression after a real improvement -> keep the improvement
        ([2, 0], 0),  # regression after intent-correct -> keep intent-correct
        ([0, 0, 0], 0),  # equal score, equal rule_ids -> earliest wins (fastest convergence)
        ([1, 1], 0),  # equal score, earlier wins (cheapest to reproduce)
    ]
    for scores, expected_idx in cases:
        iters = [{"score": s, "rule_ids": []} for s in scores]
        got = _best_iteration_index(iters)
        status = "OK" if got == expected_idx else "FAIL"
        if got != expected_idx:
            all_ok = False
        print(f"[{status}] best_iteration_index{scores}: got={got} expected={expected_idx}")
    tie_break = _best_iteration_index([{"score": 0, "rule_ids": ["A", "B"]}, {"score": 0, "rule_ids": ["A"]}])
    status = "OK" if tie_break == 1 else "FAIL"
    if tie_break != 1:
        all_ok = False
    print(f"[{status}] best_iteration_index tie-break on fewer rule_ids: got={tie_break} expected=1")

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
# Loop condition -- the harness IS the agent loop. Emulates an agentic
# lint/dry-run tool loop for models without native function calling: the model
# only ever sees chat messages; the harness runs the tools and feeds the
# diagnostics back. Initial prompt is P2_cheatsheet (closest to what an agent
# gets from the reference tool); up to LOOP_MAX_ITERATIONS generations.
# --------------------------------------------------------------------------- #


def _best_iteration_index(iterations: list[dict[str, Any]]) -> int:
    """Highest score wins; ties break on fewest error rule_ids (closer to passing), then
    earliest index (rewards fast convergence, cheapest to reproduce)."""
    return max(
        range(len(iterations)),
        key=lambda i: (iterations[i]["score"], -len(iterations[i]["rule_ids"]), -i),
    )


def run_loop_cell(model: str, task: dict[str, Any]) -> dict[str, Any]:
    """One model x task loop cell. Returns the BEST-scoring generation across all
    iterations (not the last -- a later attempt can regress after a real fix; see
    haiku-cli-track-20260712.md), iterations used, per-iteration record, summed latency."""
    messages: list[dict[str, str]] = [{"role": "user", "content": _p2(task["prompt"])}]
    iterations: list[dict[str, Any]] = []
    total_latency = 0
    timed_out = False
    err_note: str | None = None

    for attempt in range(1, LOOP_MAX_ITERATIONS + 1):
        content, latency_ms, err = call_ollama(model, messages, num_ctx=NUM_CTX_LOOP)
        total_latency += latency_ms
        if err is not None:
            timed_out = err == "timeout"
            if not iterations:  # nothing to score at all
                return {
                    "score": "timeout" if timed_out else "error",
                    "rule_ids": [],
                    "detail": err,
                    "iterations": 0,
                    "iteration_details": [],
                    "latency_ms": total_latency,
                    "timed_out": timed_out,
                }
            err_note = f" (+ {err} at iteration {attempt})"
            break

        info = evaluate_generation(task, content or "")
        iterations.append(
            {"score": info["score"], "rule_ids": info["rule_ids"], "detail": info["detail"], "latency_ms": latency_ms}
        )
        if info["feedback"] is None:  # intent-correct (or intent check itself broke) -- stop
            break
        messages.append({"role": "assistant", "content": content or ""})
        messages.append({"role": "user", "content": info["feedback"]})

    best_idx = _best_iteration_index(iterations)
    best = iterations[best_idx]
    return {
        "score": best["score"],
        "rule_ids": best["rule_ids"],
        "detail": best["detail"] + (err_note or ""),
        "best_iteration": best_idx + 1,
        "last_score": iterations[-1]["score"],
        "iterations": len(iterations),
        "iteration_details": iterations,
        "latency_ms": total_latency,
        "timed_out": timed_out,
    }


def run_loop_matrix(models: list[str], tasks: list[dict[str, Any]], *, out_path: Path) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    def persist() -> None:
        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "condition": LOOP_VARIANT,
            "initial_variant": "P2_cheatsheet",
            "max_iterations": LOOP_MAX_ITERATIONS,
            "models": models,
            "tasks": [t["id"] for t in tasks],
            "cells": cells,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for model in models:
        consecutive_timeouts = 0
        skip_rest = False
        for task in tasks:
            cell: dict[str, Any] = {"model": model, "variant": LOOP_VARIANT, "task": task["id"]}
            if skip_rest:
                cell.update(
                    score="timeout",
                    rule_ids=[],
                    latency_ms=None,
                    iterations=0,
                    detail="skipped: 2 consecutive timeouts",
                )
                cells.append(cell)
                persist()
                continue

            print(f"-> {model} / {LOOP_VARIANT} / {task['id']}", file=sys.stderr, flush=True)
            result = run_loop_cell(model, task)
            consecutive_timeouts = consecutive_timeouts + 1 if result.pop("timed_out") else 0
            cell.update(result)
            cells.append(cell)
            print(f"   score={result['score']} iterations={result['iterations']}", file=sys.stderr)
            persist()
            if consecutive_timeouts >= 2:
                print(f"   {model}: 2 consecutive timeouts, skipping remaining cells", file=sys.stderr)
                skip_rest = True

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
        intent_by_variant: dict[str, int] = {}
        for variant in variants:
            vcells = [c for c in model_cells if c["variant"] == variant]
            intent_correct = sum(1 for c in vcells if c["score"] == 2)
            runs = sum(1 for c in vcells if c["score"] in (1, 2))
            intent_by_variant[variant] = intent_correct
            totals.append(f"{variant}: intent-correct {intent_correct}/{len(tasks)}, runs {runs}/{len(tasks)}")
        lines.append(" | ".join(totals))
        lines.append("")
        static_variants = [v for v in variants if v != LOOP_VARIANT]
        if LOOP_VARIANT in variants and static_variants and any(c["variant"] == LOOP_VARIANT for c in model_cells):
            best_static = max(static_variants, key=lambda v: intent_by_variant[v])
            lines.append(
                f"Static best ({best_static}): intent-correct {intent_by_variant[best_static]}/{len(tasks)} "
                f"vs loop: {intent_by_variant[LOOP_VARIANT]}/{len(tasks)}."
            )
            iteration_counts = sorted(
                c.get("iterations", 0) for c in model_cells if c["variant"] == LOOP_VARIANT
            )
            histogram = ", ".join(
                f"{n} iteration{'s' if n != 1 else ''}: {iteration_counts.count(n)} tasks"
                for n in sorted(set(iteration_counts))
            )
            lines.append(f"Loop iterations used: {histogram}.")
            lines.append("")
    if LOOP_VARIANT in variants:
        lines.append(
            "Reference: Haiku 4.5 track (haiku-track-20260704.md): bare 0/6, tool loop 6/6 intent-correct."
        )
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
    parser.add_argument(
        "--loop",
        action="store_true",
        help=(
            "run the loop condition (P2 initial prompt, lint/dry-run feedback, "
            "max LOOP_MAX_ITERATIONS generations per task, best-scoring generation reported)"
        ),
    )
    parser.add_argument(
        "--report",
        nargs="+",
        default=None,
        metavar="JSON",
        help="no model calls: merge the given results JSONs and rewrite results/latest.md",
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--variants", nargs="+", default=list(PROMPT_VARIANTS))
    parser.add_argument("--tasks", nargs="+", default=[t["id"] for t in TASKS])
    parser.add_argument("--out", default=None, help="results json path (default: results/<timestamp>.json)")
    args = parser.parse_args()

    if args.selftest:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    if args.report:
        cells = []
        for path in args.report:
            cells.extend(json.loads(Path(path).read_text(encoding="utf-8"))["cells"])
        models = list(dict.fromkeys(c["model"] for c in cells))
        present = {c["variant"] for c in cells}
        variants = [v for v in [*PROMPT_VARIANTS, LOOP_VARIANT] if v in present]
        tasks = [t for t in TASKS if t["id"] in {c["task"] for c in cells}]
        report = render_report(cells, models, variants, tasks)
        print(report)
        (RESULTS_DIR / "latest.md").write_text(report, encoding="utf-8")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = "-loop" if args.loop else ""
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"{timestamp}{suffix}.json"

    if args.smoke:
        models, variants, tasks = ["gemma4:31b"], ["P1_intent_table"], [TASKS_BY_ID["weighted_country"]]
    else:
        models = args.models
        variants = args.variants
        tasks = [TASKS_BY_ID[t] for t in args.tasks]

    if args.loop:
        cells = run_loop_matrix(models, tasks, out_path=out_path)
        variants = [LOOP_VARIANT]
    else:
        cells = run_matrix(models, variants, tasks, out_path=out_path)
    report = render_report(cells, models, variants, tasks)
    print(report)
    if not args.loop:  # loop runs are merged into latest.md via --report, not on their own
        (RESULTS_DIR / "latest.md").write_text(report, encoding="utf-8")
    print(f"\nresults json: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
