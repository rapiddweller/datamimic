# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Before/after message harness for constraint migration.

This is a TEMPORARY MIGRATION AID, not a permanent test suite. It exists only to
verify that migrating cross-field facts from imperative ModelUtil methods to
declarative constraints preserves the exact error messages.

The harness:
1. Defines a battery of failing input dicts for each migrating validator
2. Calls the CURRENT ModelUtil methods, captures exact raised messages
3. Writes them to a JSON snapshot file (--snapshot mode)
4. Compares snapshot.json against expected messages (--compare mode)

Post-migration, a later agent will re-run this in compare mode to ensure messages
haven't drifted.

USAGE:
    python3 migration_harness.py --snapshot     # Create baseline snapshot
    python3 migration_harness.py --compare      # Verify no message drift
"""

import argparse
import json
import sys
from pathlib import Path

from datamimic_ce.constants.attribute_constants import (
    ATTR_COUNT,
    ATTR_CYCLIC,
    ATTR_DEFAULT_VALUE,
    ATTR_DISTRIBUTION,
    ATTR_MAX_COUNT,
    ATTR_MIN_COUNT,
    ATTR_SOURCE,
    ATTR_UNIQUE,
    ATTR_VALUES,
    ATTR_WEIGHTS,
)
from datamimic_ce.model.model_util import ModelUtil

# Battery of failing inputs for each migrating validator from the A2 plan list
FAILING_INPUTS = {
    "check_weights_require_values": [
        {
            "input": {ATTR_WEIGHTS: "1,2"},  # weights without values
            "description": "weights without values",
        },
    ],
    "check_min_max_count": [
        {
            "input": {ATTR_COUNT: "5", ATTR_MIN_COUNT: 3},
            "element_tag": "generate",
            "description": "count + minCount together",
        },
        {
            "input": {ATTR_COUNT: "5", ATTR_MAX_COUNT: 10},
            "element_tag": "generate",
            "description": "count + maxCount together",
        },
        {
            "input": {ATTR_MIN_COUNT: 10, ATTR_MAX_COUNT: 3},
            "element_tag": "nestedKey",
            "description": "minCount > maxCount",
        },
    ],
    "check_unique_constraints": [
        {
            "input": {ATTR_UNIQUE: "true"},
            "description": "unique without values or source",
        },
        {
            "input": {ATTR_UNIQUE: "true", ATTR_VALUES: "'a'", ATTR_WEIGHTS: "1"},
            "description": "unique with weights",
        },
        {
            "input": {ATTR_UNIQUE: "true", ATTR_VALUES: "'a'", ATTR_CYCLIC: "true"},
            "description": "unique with cyclic",
        },
        {
            "input": {ATTR_UNIQUE: "true", ATTR_VALUES: "'a'", ATTR_DISTRIBUTION: "cumulated"},
            "description": "unique with non-random distribution",
        },
    ],
    "check_exist_count": [
        {
            "input": {},
            "description": "no count, source, script, minCount, or maxCount",
        },
    ],
    "check_valid_default_value": [
        {
            "input": {ATTR_DEFAULT_VALUE: "fallback"},
            "description": "defaultValue without script",
        },
    ],
    "check_generation_mode_of_source": [
        {
            "input": {ATTR_SOURCE: "db1", "type": "string", "selector": "col"},
            "description": "source with both type and selector",
        },
    ],
}


def capture_current_messages() -> dict[str, list[dict]]:
    """Run current ModelUtil methods against failing inputs, capture messages.

    Returns a dict mapping validator_name -> list of {input, description, message}.
    """
    results = {}

    # check_weights_require_values
    messages = []
    for test_case in FAILING_INPUTS["check_weights_require_values"]:
        try:
            ModelUtil.check_weights_require_values(test_case["input"])
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": None,
                    "error": "No error raised (expected failure)",
                }
            )
        except ValueError as e:
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": str(e),
                }
            )
    results["check_weights_require_values"] = messages

    # check_min_max_count
    messages = []
    for test_case in FAILING_INPUTS["check_min_max_count"]:
        try:
            ModelUtil.check_min_max_count(test_case["input"], test_case["element_tag"])
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": None,
                    "error": "No error raised (expected failure)",
                }
            )
        except ValueError as e:
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": str(e),
                }
            )
    results["check_min_max_count"] = messages

    # check_unique_constraints
    messages = []
    for test_case in FAILING_INPUTS["check_unique_constraints"]:
        try:
            ModelUtil.check_unique_constraints(test_case["input"])
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": None,
                    "error": "No error raised (expected failure)",
                }
            )
        except ValueError as e:
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": str(e),
                }
            )
    results["check_unique_constraints"] = messages

    # check_exist_count
    messages = []
    for test_case in FAILING_INPUTS["check_exist_count"]:
        try:
            ModelUtil.check_exist_count(test_case["input"])
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": None,
                    "error": "No error raised (expected failure)",
                }
            )
        except ValueError as e:
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": str(e),
                }
            )
    results["check_exist_count"] = messages

    # check_valid_default_value
    messages = []
    for test_case in FAILING_INPUTS["check_valid_default_value"]:
        try:
            ModelUtil.check_valid_default_value(test_case["input"])
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": None,
                    "error": "No error raised (expected failure)",
                }
            )
        except ValueError as e:
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": str(e),
                }
            )
    results["check_valid_default_value"] = messages

    # check_generation_mode_of_source
    messages = []
    for test_case in FAILING_INPUTS["check_generation_mode_of_source"]:
        try:
            ModelUtil.check_generation_mode_of_source(test_case["input"])
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": None,
                    "error": "No error raised (expected failure)",
                }
            )
        except ValueError as e:
            messages.append(
                {
                    "input": test_case["input"],
                    "description": test_case["description"],
                    "message": str(e),
                }
            )
    results["check_generation_mode_of_source"] = messages

    return results


def save_snapshot(snapshot_path: Path) -> None:
    """Capture current messages and write to snapshot file."""
    messages = capture_current_messages()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, "w") as f:
        json.dump(messages, f, indent=2)
    print(f"Snapshot created: {snapshot_path}")
    print(f"Total validators: {len(messages)}")
    total_cases = sum(len(cases) for cases in messages.values())
    print(f"Total test cases: {total_cases}")


def compare_snapshot(snapshot_path: Path) -> None:
    """Compare current messages against snapshot."""
    if not snapshot_path.exists():
        print(f"ERROR: snapshot not found at {snapshot_path}")
        sys.exit(1)

    with open(snapshot_path) as f:
        snapshot = json.load(f)

    current = capture_current_messages()

    all_match = True
    for validator_name in sorted(set(list(snapshot.keys()) + list(current.keys()))):
        if validator_name not in snapshot:
            print(f"\nNEW VALIDATOR: {validator_name}")
            all_match = False
            continue
        if validator_name not in current:
            print(f"\nDELETED VALIDATOR: {validator_name}")
            all_match = False
            continue

        snapshot_cases = snapshot[validator_name]
        current_cases = current[validator_name]

        if len(snapshot_cases) != len(current_cases):
            print(
                f"\n{validator_name}: case count mismatch "
                f"(snapshot: {len(snapshot_cases)}, current: {len(current_cases)})"
            )
            all_match = False
            continue

        for snap_case, curr_case in zip(snapshot_cases, current_cases, strict=True):
            snap_msg = snap_case.get("message")
            curr_msg = curr_case.get("message")
            if snap_msg != curr_msg:
                print(f"\n{validator_name} ({snap_case.get('description')}):")
                print(f"  Snapshot: {snap_msg}")
                print(f"  Current:  {curr_msg}")
                all_match = False

    if all_match:
        print("✓ All messages match snapshot")
    else:
        print("\n✗ Message mismatches detected")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Constraint migration message harness")
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Create baseline snapshot of current messages",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare current messages against snapshot",
    )
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=Path(__file__).parent / "migration_messages_snapshot.json",
        help="Path to snapshot file (default: migration_messages_snapshot.json in same dir)",
    )

    args = parser.parse_args()

    if args.snapshot:
        save_snapshot(args.snapshot_path)
    elif args.compare:
        compare_snapshot(args.snapshot_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
