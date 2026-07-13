"""Stress test: novel business scenarios, never seen by bench.py's tuned TASKS/golden
descriptors, run against a local model two ways:

  scaffold - structured JSON output under scaffold.SPEC_JSON_SCHEMA, then
             scaffold.check() (render -> lint -> dry-run) - the newly-wired path.
  raw_xml  - free-form XML authoring against the cheatsheet (reference("overview")),
             lint_source + dry_run_source directly - the pre-existing path.

No intent_check scoring (these scenarios are one-off, not worth permanent scoring
code for) - reports structural pass/fail per stage plus a sample of the actual
output for manual eyeballing.

Usage: RUNTIME_ENVIRONMENT=development uv run python3 benchmarks/dsl-authoring/stress_scaffold.py [--model gemma4:31b]
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

OLLAMA_URL = "http://localhost:11434/api/chat"
TEMPERATURE, TOP_P, TOP_K, SEED = 1.0, 0.95, 64, 42  # matches bench.py's Gemma-4-documented settings
NUM_PREDICT = 1400
NUM_CTX = 12000
CALL_TIMEOUT_S = 300

SCENARIOS = [
    {
        "id": "library_loans",
        "prompt": (
            "A library system: 20 books (title, isbn pattern, genre one of "
            "fiction/nonfiction/reference), then loans reading books back from storage — "
            "each loan carries the book's real title and genre (joined by the book). JSON."
        ),
    },
    {
        "id": "restaurant_orders",
        "prompt": (
            "A restaurant: 15 orders, each with 1-4 line items, each line item has a dish "
            "name (one of pasta/pizza/salad/soup, weighted so pizza is twice as common as "
            "the others) and a quantity 1-3. JSON."
        ),
    },
    {
        "id": "server_metrics_week",
        "prompt": (
            "Hourly CPU and memory usage for 3 servers over one full week: timestamp, "
            "server number, cpu percent (0-100 decimal), memory percent (0-100 decimal). JSON."
        ),
    },
    {
        "id": "org_chart",
        "prompt": (
            "12 departments, each with a real department head (a person's name) and "
            "2-5 employees per department, each employee also a real person name with a "
            "unique employee id. JSON."
        ),
    },
    {
        "id": "cart_abandonment",
        "prompt": (
            "20 shopping cart sessions with a cart_total (decimal 10-500) written to storage, "
            "then a second step reads them back and flags each as abandoned (true) if "
            "cart_total is over 100, else completed (false). JSON."
        ),
    },
    {
        "id": "flight_seats",
        "prompt": (
            "8 flights with a unique flight number pattern (2 letters + 4 digits) and a "
            "destination from a fixed set of 5 cities, then 30-60 passengers per flight each "
            "with a unique seat number 1-180 (no two passengers on the same flight share a "
            "seat). JSON."
        ),
    },
]


def call_ollama(model: str, prompt: str, *, response_format: dict | None = None) -> tuple[str | None, int, str | None]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {
            "temperature": TEMPERATURE, "top_p": TOP_P, "top_k": TOP_K, "seed": SEED,
            "num_predict": NUM_PREDICT, "num_ctx": NUM_CTX,
        },
    }
    if response_format is not None:
        body["format"] = response_format
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=CALL_TIMEOUT_S) as resp:
            data = json.loads(resp.read())
        latency_ms = int((time.perf_counter() - started) * 1000)
        return data.get("message", {}).get("content", ""), latency_ms, None
    except (urllib.error.URLError, OSError, TimeoutError) as err:
        return None, int((time.perf_counter() - started) * 1000), str(err)
    except Exception as err:
        return None, int((time.perf_counter() - started) * 1000), str(err)


# Mechanical, non-semantic checks that the model at least ATTEMPTED the right mechanism
# for scenarios known to require memstore read-back / time-series / unique — not a
# bench.py-style intent_check (too large a scope, see the plan's "explicitly out of
# scope"), just enough to turn "eyeball six JSON blobs" into a printed pass/fail. Checked
# against the rendered XML (post-normalization), not the model's raw JSON, so a near-miss
# key _normalize() already fixed doesn't read as a false failure here.
_SPEC_SHAPE_CHECKS = {
    "library_loans": lambda xml: "source=" in xml or "expected a source= read-back somewhere, found none",
    "cart_abandonment": lambda xml: "source=" in xml or "expected a source= read-back somewhere, found none",
    "server_metrics_week": lambda xml: (
        all(f"{a}=" in xml for a in ("start", "end", "interval"))
        or "expected start=/end=/interval= all set, found incomplete/missing"
    ),
    "flight_seats": lambda xml: (
        'distribution="shuffle"' in xml
        or "expected a unique (distribution=shuffle) seat number field, found none"
    ),
    "org_chart": lambda xml: (
        xml.count('entity="Person"') >= 2
        or "expected >=2 Person variable declarations (outer + nested-scoped), found fewer"
    ),
}


def _check_spec_shape(scenario_id: str, xml: str | None) -> str | None:
    """None = check passed or doesn't apply to this scenario; else a short failure reason."""
    check_fn = _SPEC_SHAPE_CHECKS.get(scenario_id)
    if check_fn is None or xml is None:
        return None
    result = check_fn(xml)
    return None if result is True else result


def run_scaffold_condition(model: str, scenario: dict) -> dict:
    from datamimic_ce.authoring.scaffold import SPEC_JSON_SCHEMA, SPEC_PROMPT_GUIDE, check

    prompt = (
        "Produce a JSON spec (matching the given schema) for this data-generation task.\n\n"
        f"{SPEC_PROMPT_GUIDE}\n"
        "Output ONLY the JSON object, no prose.\nTask: " + scenario["prompt"]
    )
    content, latency_ms, err = call_ollama(model, prompt, response_format=SPEC_JSON_SCHEMA)
    if err or content is None:
        return {"stage": "call", "ok": False, "error": err, "latency_ms": latency_ms}
    try:
        spec = json.loads(content)
    except json.JSONDecodeError as e:
        return {"stage": "parse", "ok": False, "error": str(e), "raw": content, "latency_ms": latency_ms}
    result = check(spec, dry_run=True, max_count=10, sample_rows=3)
    out = {"stage": result.stage, "ok": result.ok, "latency_ms": latency_ms, "spec": spec, "xml": result.xml}
    if result.stage == "render":
        out["error"] = result.render_error
    elif not result.ok:
        diags = result.lint_result.diagnostics if result.stage == "lint" else result.dryrun_result.diagnostics
        out["diagnostics"] = [f"{d.rule}: {d.message}" for d in diags[:5]]
    elif result.stage == "dry_run":
        out["products"] = [
            {"name": p.name, "count": p.count, "sample": p.sample[:1]} for p in result.dryrun_result.products
        ]
    out["shape_check"] = _check_spec_shape(scenario["id"], out.get("xml"))
    return out


def run_raw_xml_condition(model: str, scenario: dict) -> dict:
    from datamimic_ce.authoring import lint_source
    from datamimic_ce.authoring.dryrun import dry_run_source
    from datamimic_ce.authoring.reference import cheatsheet

    prompt = (
        f"{cheatsheet()}\n\nWrite a DATAMIMIC XML descriptor (<setup> root) for this task. "
        f"Output ONLY the XML.\nTask: {scenario['prompt']}"
    )
    content, latency_ms, err = call_ollama(model, prompt)
    if err or content is None:
        return {"stage": "call", "ok": False, "error": err, "latency_ms": latency_ms}

    import re
    m = re.search(r"<setup\b", content, re.IGNORECASE)
    if not m:
        return {"stage": "extract", "ok": False, "error": "no <setup> found", "raw": content, "latency_ms": latency_ms}
    frag = content[m.start():]
    end = frag.lower().find("</setup>")
    xml = frag[: end + len("</setup>")] if end != -1 else frag.rstrip() + "\n</setup>"

    lint = lint_source(xml)
    if not lint.ok:
        errors = [d for d in lint.diagnostics if d.severity.value == "error"]
        return {"stage": "lint", "ok": False, "xml": xml, "latency_ms": latency_ms,
                "diagnostics": [f"{d.rule}: {d.message}" for d in errors[:5]]}
    dr = dry_run_source(xml, max_count=10, sample_rows=3)
    out = {"stage": "dry_run", "ok": dr.ok, "xml": xml, "latency_ms": latency_ms}
    if not dr.ok:
        out["diagnostics"] = [f"{d.rule}: {d.message}" for d in dr.diagnostics[:5]]
    else:
        out["products"] = [{"name": p.name, "count": p.count, "sample": p.sample[:1]} for p in dr.products]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma4:31b")
    ap.add_argument("--scenarios", nargs="*", default=None, help="subset of scenario ids")
    args = ap.parse_args()

    scenarios = [s for s in SCENARIOS if args.scenarios is None or s["id"] in args.scenarios]
    results = []
    for scenario in scenarios:
        print(f"\n=== {scenario['id']} ===")
        print(f"prompt: {scenario['prompt']}")

        scaf = run_scaffold_condition(args.model, scenario)
        print(f"  scaffold: ok={scaf['ok']} stage={scaf['stage']} latency={scaf.get('latency_ms')}ms")
        if not scaf["ok"]:
            print(f"    error/diagnostics: {scaf.get('error') or scaf.get('diagnostics')}")
        else:
            print(f"    products: {scaf.get('products')}")
        if scaf.get("shape_check"):
            print(f"    SHAPE CHECK FAILED: {scaf['shape_check']}")

        raw = run_raw_xml_condition(args.model, scenario)
        print(f"  raw_xml:  ok={raw['ok']} stage={raw['stage']} latency={raw.get('latency_ms')}ms")
        if not raw["ok"]:
            print(f"    error/diagnostics: {raw.get('error') or raw.get('diagnostics')}")
        else:
            print(f"    products: {raw.get('products')}")

        results.append({"id": scenario["id"], "scaffold": scaf, "raw_xml": raw})

    scaf_ok = sum(1 for r in results if r["scaffold"]["ok"])
    raw_ok = sum(1 for r in results if r["raw_xml"]["ok"])
    shape_failures = [r["id"] for r in results if r["scaffold"].get("shape_check")]
    print(f"\n=== summary ({args.model}) — single seeded run, not a statistical claim ===")
    print(f"scaffold: {scaf_ok}/{len(results)} structurally ok")
    print(f"raw_xml:  {raw_ok}/{len(results)} structurally ok")
    if shape_failures:
        print(f"scaffold mechanical shape-check failures: {shape_failures}")
    else:
        print("scaffold mechanical shape-checks: all passed (or n/a)")

    # Timestamped, not a fixed per-model path: a fixed path silently clobbers the previous
    # run's evidence on every re-run (this cost the library_loans evidence once already).
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = (
        Path(__file__).parent / "results" / f"stress-scaffold-{args.model.replace(':', '-')}-{stamp}.json"
    )
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nfull results: {out_path}")


if __name__ == "__main__":
    main()
