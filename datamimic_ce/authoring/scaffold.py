# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Compatibility facade for the versioned authoring compiler.

Schema, normalization, and compilation are owned by their dedicated modules.
This module intentionally contains only zero-logic re-exports/delegations for
existing callers of ``authoring.scaffold``.
"""

from typing import Any

from datamimic_ce.authoring.spec import SPEC_JSON_SCHEMA, SPEC_PROMPT_GUIDE


def render(spec: dict[str, Any]) -> str:
    """Compatibility delegation to the application-owned compile path."""

    from datamimic_ce.authoring.service import compile_document

    return compile_document(spec).xml


__all__ = [
    "SPEC_JSON_SCHEMA",
    "SPEC_PROMPT_GUIDE",
    "render",
]
