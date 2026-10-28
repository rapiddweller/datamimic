# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

GUIDANCE_IN_DATE_FORMAT = "Ensure input values match inDateFormat (use %y for 2-digit years if needed)."
GUIDANCE_OUT_DATE_FORMAT = "Set inDateFormat or generate datetime values before applying outDateFormat."
GUIDANCE_EMPTY_VALUE = "Provide a non-empty value or remove date format attributes."
GUIDANCE_VALID_LOCALE = "Use a valid locale like 'en_US'."
GUIDANCE_PROJECT_ENV = "Check your project environment configuration or uploaded assets."

# count is evaluated in the enclosing record, so the generic hint (parent.name) points one level too high.
GUIDANCE_COUNT_SCOPE = (
    "count is evaluated in the enclosing record: reference its fields bare or as this.name "
    "(e.g. int(headcount)); parent.name already points one level above that record."
)

GUIDANCE_DESCRIPTOR_ENV = "Check the descriptor file in your project environment configuration or uploaded assets."

# The one way CE joins a second file; tests_ce/scenarios/s31_file_lookup builds this text.
FILE_LOOKUP_PATTERN = (
    "To look up a row of another file by a key, read the whole file once with "
    '<variable name="branches" source="data/entity/branches.ent.csv" storage="data" distribution="ordered"/> '
    "and select the row in a script: "
    '<variable name="branch" script="{b.branch_id: b for b in branches}.get(branch_id)"/>. '
    "branch is None when no row has the key: branch.city if branch else 'UNKNOWN'."
)
_LOOKUP_REFERENCE = "datamimic authoring reference --topic learning --name lookup"
GUIDANCE_FILE_LOOKUP = f"{FILE_LOOKUP_PATTERN} Read {_LOOKUP_REFERENCE}."
# Refusals of a join attempt that is not a script or where= mistake only point to the lookup (campaign b3, e07).
GUIDANCE_LOOKUP_POINTER = f"To look up a row of another file by a key, read {_LOOKUP_REFERENCE}."
# where= reads one row, so the generic hint (parent.name, root.name) sends a lookup to a dead end (campaign b3, e07).
GUIDANCE_WHERE_SCOPE = (
    "where= reads only the current file row: its columns bare or as this.<column>, and the expression functions; "
    "parent., root., a <variable> and a setup name do not exist there. A row of another file with the key of the "
    f"current record is a lookup, not a filter. {GUIDANCE_FILE_LOOKUP}"
)
# Build shows no engine message, so this names the replacements of the builtins agents reach for (campaign b3, e07).
GUIDANCE_SCRIPT_BUILTIN = (
    "Write next(...) as ([x for x in rows if ...] or [None])[0] and isinstance(x, str) as type(x) is str. "
    f"{GUIDANCE_FILE_LOOKUP}"
)
