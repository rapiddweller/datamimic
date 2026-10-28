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
GUIDANCE_FILE_LOOKUP = f"{FILE_LOOKUP_PATTERN} Read datamimic authoring reference --topic learning --name lookup."
