# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM4xx — cross-statement rules: references between elements the engine only
checks at runtime (unknown targets) or not at all (duplicate names)."""

from collections.abc import Iterable

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.element_constants import (
    EL_DATABASE,
    EL_GENERATE,
    EL_INCLUDE,
    EL_ITERATE,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_VARIABLE,
)
from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
)
from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS, ExporterUtil

_GENERATES = (EL_GENERATE, EL_ITERATE)
_SOURCE_READERS = (*_GENERATES, EL_VARIABLE, EL_NESTED_KEY)
# Engine source dispatch (task_util.gen_task_load_data_from_source_or_script): a source is a
# file (by extension), else a memstore/client id. `.dbunit.xml` is matched before `.xml`.
_SOURCE_FILE_SUFFIXES = (".csv", ".json", ".xlsx", ".dbunit.xml", ".xml")
_STATIC_TARGETS = {
    *_BUFFERED_EXPORTERS,
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
}


def _declared_ids(ctx: LintContext) -> tuple[set[str], set[str]]:
    """(client ids, memstore ids) declared in the descriptor."""
    clients = {el.get("id") for el in ctx.iter(EL_DATABASE, EL_MONGODB) if el.get("id")}
    memstores = {el.get("id") for el in ctx.iter(EL_MEMSTORE) if el.get("id")}
    return {c for c in clients if c}, {m for m in memstores if m}


class UnknownTarget(Rule):
    id = "DM401"
    severity = Severity.ERROR
    docs = "reference://targets"

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        clients, memstores = _declared_ids(ctx)
        for element in ctx.iter(*_GENERATES):
            target_attr = element.get("target")
            if not target_attr:
                continue
            try:
                # SPOT: the exact parser the engine uses (AST-based, param-safe)
                parsed = ExporterUtil.parse_function_string(target_attr)
            except ValueError as err:
                yield ctx.diag(
                    type(self), element, f"Cannot parse target: {err}", "Fix the target list syntax."
                )
                continue
            for entry in parsed:
                name = entry["function_name"]
                base = name.split(".", 1)[0]
                if "." in name:
                    if base not in clients:
                        yield ctx.diag(
                            type(self),
                            element,
                            f"Target '{name}' references client '{base}', but no <database>/<mongodb> "
                            f"with id=\"{base}\" is declared.",
                            f'Declare <mongodb id="{base}"/> / <database id="{base}" .../> in <setup>, '
                            "or fix the target name.",
                        )
                elif name not in _STATIC_TARGETS and name not in clients and name not in memstores:
                    valid = sorted(_STATIC_TARGETS | clients | memstores)
                    yield ctx.diag(
                        type(self),
                        element,
                        f"Unknown target '{name}'.",
                        f"Use one of: {', '.join(valid)}, or declare a client/memstore with that id.",
                    )


class DuplicateGenerateName(Rule):
    id = "DM403"
    severity = Severity.WARNING

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for parent in ctx.iter():
            seen: dict[str, etree._Element] = {}
            for child in parent:
                if not isinstance(child.tag, str) or child.tag not in _GENERATES:
                    continue
                name = child.get("name")
                if name is None:
                    continue
                if name in seen:
                    yield ctx.diag(
                        type(self),
                        child,
                        f"Duplicate <generate name=\"{name}\"> in the same scope — products and "
                        "test captures overwrite/merge by name.",
                        "Give every sibling <generate> a unique name.",
                    )
                seen.setdefault(name, child)


class UnknownSource(Rule):
    id = "DM402"
    severity = Severity.ERROR
    docs = "reference://targets"

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        clients, memstores = _declared_ids(ctx)
        for element in ctx.iter(*_SOURCE_READERS):
            source = element.get("source")
            if not source or source.endswith(_SOURCE_FILE_SUFFIXES):
                continue  # empty, or a file (existence is a separate concern)
            if source not in clients and source not in memstores:
                valid = sorted(clients | memstores)
                declared = f"Declared ids: {', '.join(valid)}. " if valid else ""
                yield ctx.diag(
                    type(self),
                    element,
                    f"source=\"{source}\" is neither a data file (.csv/.json/.xlsx/.xml/.dbunit.xml) "
                    "nor a declared <memstore>/<database>/<mongodb> id.",
                    f"{declared}Point source= at a real file, or declare the client/memstore with that id.",
                )


class MissingInclude(Rule):
    id = "DM405"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        if ctx.base_dir is None:
            return  # inline XML: relative includes are not resolvable, don't false-positive
        for element in ctx.iter(EL_INCLUDE):
            uri = element.get("uri")
            if not uri or "{" in uri:  # dynamic {var} uris resolve at runtime
                continue
            if not (ctx.base_dir / uri).is_file():
                yield ctx.diag(
                    type(self),
                    element,
                    f"<include uri=\"{uri}\"> points at a file that does not exist next to the descriptor.",
                    "Fix the path (relative to the descriptor's directory) or create the included file.",
                )


RULES: tuple[type[Rule], ...] = (
    UnknownTarget,
    UnknownSource,
    MissingInclude,
    DuplicateGenerateName,
)
