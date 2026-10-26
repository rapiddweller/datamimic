# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Bind complete CE descriptor facts and transaction requirements to acceptance."""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import NoReturn

from pydantic import JsonValue, TypeAdapter, ValidationError

from datamimic_ce.authoring.domain.acceptance_contract import (
    AcceptanceCheckV1,
    AcceptanceJoinV1,
    AcceptanceListV1,
    AcceptanceProductV1,
    AcceptanceProjectionError,
    AcceptanceReadbackV1,
    AcceptanceRelationshipV1,
    AcceptanceSpecV1,
    validate_acceptance_check,
    validate_acceptance_subject,
)
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, DmJsonNodeV1
from datamimic_ce.authoring.domain.expectations import (
    AllowedValuesExpectation,
    DeclaredSinkIdentity,
    ExactCountExpectation,
    ExpectationIntent,
    FieldSelection,
    ForeignKeyExpectation,
    PerParentCountExpectation,
    PerParentRowsSubject,
    ProductRowsSubject,
    RangeExpectation,
    UniqueExpectation,
    expectation_identity,
)
from datamimic_ce.authoring.domain.proof import AcceptanceOrigin, ForeignKeyRole, IdentifierRole
from datamimic_ce.authoring.domain.requests import BuildRequestV5
from datamimic_ce.authoring.domain.script_semantics import (
    ScriptScope,
    is_exact_scope_field_reference,
    names_statement_operation,
    references_current_scope_field,
)
from datamimic_ce.engine.dsl.api import (
    NAME_SEPARATOR,
    GenerateStatement,
    TimeSeriesConfig,
    TimeSeriesConfigError,
    capture_product_name,
    parse_literal_values,
)


@dataclass(frozen=True)
class _Product:
    node: DmJsonNodeV1
    path: tuple[str | int, ...]
    product: AcceptanceProductV1
    parent: str | None
    count: int | None


def _reject(message: str, path: tuple[str | int, ...], remediation: str | None = None) -> NoReturn:
    raise AcceptanceProjectionError(
        (
            catalog_diagnostic(
                AuthoringRuleId.INPUT,
                message,
                phase=DiagnosticPhase.EXPECTATION,
                path=path,
                remediation=remediation,
            ),
        )
    )


def _name(node: DmJsonNodeV1, path: tuple[str | int, ...]) -> str:
    name = node.properties.get("name")
    if not isinstance(name, str) or not name:
        _reject("Acceptance requires a named product or field.", path + ("properties", "name"))
        raise AssertionError
    return name


def _fields(node: DmJsonNodeV1) -> tuple[str, ...]:
    if node.kind == "condition":
        # Branches are exclusive; retain duplicates within each branch.
        alternatives: Counter[str] = Counter()
        for branch in node.children:
            alternatives |= Counter(_fields(branch))
        return tuple(alternatives.elements())
    fields: list[str] = []
    for child in node.children:
        if child.kind == "generate":
            continue
        name = child.properties.get("name")
        if child.kind in {"key", "nestedKey", "array"} and isinstance(name, str):
            fields.append(name)
        elif child.kind == "reference":
            mapped = tuple(item.properties.get("target") for item in child.children if item.kind == "field")
            fields.extend(item for item in mapped if isinstance(item, str))
            if not mapped and isinstance(name, str):
                fields.append(name)
        elif child.kind not in {"variable", "element"}:
            fields.extend(_fields(child))
    return tuple(fields)


def _integer(value: object) -> int | None:
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return int(value)
    return None


def _count(node: DmJsonNodeV1, path: tuple[str | int, ...]) -> int | None:
    if node.properties.get("source") is not None:
        return None
    count = _integer(node.properties.get("count"))
    start, end, interval = (node.properties.get(key) for key in ("start", "end", "interval"))
    if isinstance(start, str) and isinstance(end, str) and isinstance(interval, str):
        if "count" in node.properties and count is None:
            return None
        try:
            window = TimeSeriesConfig.parse(start, end, interval)
        except TimeSeriesConfigError as error:
            _reject(str(error), path + ("properties", error.attribute))
        return window.ticks_per_series * (count if count is not None else 1)
    return count


def _count_per_invocation(node: DmJsonNodeV1) -> int | None:
    if node.properties.get("source") is not None:
        return _integer(node.properties.get("traversal_count"))
    count = _integer(node.properties.get("count"))
    if count is None and "count" not in node.properties and "start" in node.properties:
        return 1
    return count


def _parent_reference(script: object) -> str | None:
    if not isinstance(script, str):
        return None
    try:
        node = ast.parse(script, mode="eval").body
    except SyntaxError:
        return None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "parent":
        return node.attr
    return None


def _memstore_entity(node: DmJsonNodeV1, name: str) -> str:
    target_entity = node.properties.get("target_entity")
    return GenerateStatement.memstore_entity(target_entity if isinstance(target_entity, str) else None, name)


def _target_entity(node: DmJsonNodeV1, name: str) -> str:
    """A database or MongoDB sink's entity; type takes part here, unlike a memstore write."""
    for attribute in ("target_entity", "type"):
        value = node.properties.get(attribute)
        if isinstance(value, str) and value:
            return value
    return name


def _products(document: DmJsonDocumentV1, included: tuple[tuple[str, DmJsonDocumentV1], ...]) -> tuple[_Product, ...]:
    declarations = {
        node.properties.get("id"): node.kind for node in document.root.children if node.kind in {"database", "mongodb"}
    }
    entries: list[_Product] = []

    def visit(node: DmJsonNodeV1, path: tuple[str | int, ...], parent: _Product | None) -> None:
        # A source-free clear or drop produces no rows: it is an operation, not a product to prove.
        target = node.properties.get("target")
        if node.kind == "generate" and not (isinstance(target, str) and names_statement_operation(target)):
            name = _name(node, path)
            runtime_name = NAME_SEPARATOR.join((parent.product.runtime_name, name)) if parent else name
            entity = _target_entity(node, name)
            targets = node.properties.get("target", "")
            sinks: list[DeclaredSinkIdentity] = []
            if isinstance(targets, str) and isinstance(entity, str):
                for target in targets.split(","):
                    target = target.strip()
                    family = declarations.get(target)
                    if family == "database":
                        sinks.append(DeclaredSinkIdentity(kind="database", environment=target, entity=entity))
                    elif family == "mongodb":
                        sinks.append(DeclaredSinkIdentity(kind="mongodb", environment=target, entity=entity))
            lists = tuple(
                AcceptanceListV1(
                    name=_name(child, path),
                    fields=_fields(child),
                    count_per_row=_count(child, path + ("children", index)),
                )
                for index, child in enumerate(node.children)
                if child.kind == "nestedKey" and child.properties.get("type") == "list"
            )
            fields = _fields(node)
            if len(fields) != len(set(fields)):
                _reject("Declared output fields must be unique for acceptance.", path + ("children",))
            product = AcceptanceProductV1(
                name=name,
                runtime_name=runtime_name,
                capture_name=capture_product_name(runtime_name),
                count_per_invocation=_count_per_invocation(node),
                fields=fields,
                lists=lists,
                declared_sinks=tuple(sinks),
            )
            entry = _Product(node, path, product, parent.product.name if parent else None, _count(node, path))
            entries.append(entry)
            parent = entry
        for index, child in enumerate(node.children):
            visit(child, path + ("children", index), parent)

    visit(document.root, ("document", "root"), None)
    for uri, step in included:
        visit(step.root, ("include", uri, "root"), None)
    return tuple(entries)


def project_acceptance(
    request: BuildRequestV5,
    canonical_document: DmJsonDocumentV1,
    included: tuple[tuple[str, DmJsonDocumentV1], ...] = (),
) -> AcceptanceSpecV1:
    """Acceptance over the products of the entry and of every included step, keyed by their literal uri."""
    entries = _products(canonical_document, included)
    seen: set[str] = set()
    for entry in entries:
        if entry.product.name in seen:
            _reject(
                "Product names must be globally unique for bounded capture.",
                entry.path + ("properties", "name"),
                remediation=(
                    "Rename one of the products; Build addresses every product, nested products included, "
                    "by its own name."
                ),
            )
        seen.add(entry.product.name)
    relationships: list[AcceptanceRelationshipV1] = []
    checks: list[AcceptanceCheckV1] = []

    def derive(expectation: ExpectationIntent, path: tuple[str | int, ...]) -> None:
        checks.append(AcceptanceCheckV1(expectation=expectation, path=path, origin=AcceptanceOrigin.DERIVED))

    counts: dict[str, int] = {}
    for entry in entries:
        name = entry.product.name
        subject = ProductRowsSubject(product=name)
        if entry.parent:
            joins = tuple(
                AcceptanceJoinV1(child_field=_name(child, entry.path), parent_field=parent_field)
                for child in entry.node.children
                if child.kind == "key"
                if (parent_field := _parent_reference(child.properties.get("script"))) is not None
            )
            relationships.append(AcceptanceRelationshipV1(parent_product=entry.parent, child_product=name, joins=joins))
            if entry.count is not None:
                derive(
                    PerParentCountExpectation(
                        subject=PerParentRowsSubject(parent_product=entry.parent, child_product=name), count=entry.count
                    ),
                    entry.path,
                )
                if entry.parent in counts:
                    counts[name] = counts[entry.parent] * entry.count
        elif entry.count is not None:
            counts[name] = entry.count
        if name in counts:
            derive(ExactCountExpectation(subject=subject, count=counts[name]), entry.path)
        for index, field in enumerate(entry.node.children):
            if field.kind == "key":
                _derive_field(field, subject, entry.path + ("children", index), derive)
            elif field.kind == "nestedKey" and field.properties.get("type") == "list":
                list_name = _name(field, entry.path)
                list_subject = ProductRowsSubject(product=name, list_field=list_name)
                for inner_index, inner in enumerate(field.children):
                    if inner.kind == "key":
                        _derive_field(
                            inner, list_subject, entry.path + ("children", index, "children", inner_index), derive
                        )
    by_name = {entry.product.name: entry for entry in entries}
    for relationship in relationships:
        for join in relationship.joins:
            if join.parent_field not in by_name[relationship.parent_product].product.fields:
                _reject("Parent reference names an unknown field.", by_name[relationship.child_product].path)
    spec = AcceptanceSpecV1(products=tuple(entry.product for entry in entries), relationships=tuple(relationships))
    explicit_joins: dict[tuple[str, str], tuple[AcceptanceJoinV1, ...]] = {}
    for index, declaration in enumerate(request.product_roles):
        path = ("product_roles", index)
        subject = ProductRowsSubject(product=declaration.product, list_field=declaration.list_field)
        validate_acceptance_subject(spec, subject, path, declaration.field)
        if isinstance(declaration.role, IdentifierRole):
            derive(
                UniqueExpectation(
                    subject=subject,
                    field=declaration.field,
                    scope="per_parent" if declaration.list_field is not None else "global",
                ),
                path,
            )
        elif isinstance(declaration.role, ForeignKeyRole):
            role = declaration.role
            entry = by_name[declaration.product]
            if entry.parent == role.parent_product and declaration.list_field is None:
                field_node = next(
                    (item for item in entry.node.children if item.properties.get("name") == declaration.field), None
                )
                script = field_node.properties.get("script") if field_node else None
                if not isinstance(script, str) or not is_exact_scope_field_reference(
                    script, ScriptScope.PARENT, role.parent_field
                ):
                    _reject("A nested foreign-key role must copy the exact parent field using parent.field.", path)
            parent_subject = ProductRowsSubject(product=role.parent_product)
            validate_acceptance_subject(spec, parent_subject, path + ("role",), role.parent_field)
            derive(
                ForeignKeyExpectation(
                    child=FieldSelection(subject=subject, field=declaration.field),
                    parent=FieldSelection(subject=parent_subject, field=role.parent_field),
                ),
                path,
            )
            if entry.parent == role.parent_product and declaration.list_field is None:
                identity = (role.parent_product, declaration.product)
                join = AcceptanceJoinV1(child_field=declaration.field, parent_field=role.parent_field)
                declared = explicit_joins.get(identity, ())
                if join not in declared:
                    explicit_joins[identity] = (*declared, join)
    for index_rel, relationship in enumerate(relationships):
        identity = (relationship.parent_product, relationship.child_product)
        if identity in explicit_joins:
            # Declared FK roles select identity; other parent copies carry ordinary data.
            relationships[index_rel] = relationship.model_copy(update={"joins": explicit_joins[identity]})
    checks.extend(
        AcceptanceCheckV1(expectation=item, path=("expectations", index))
        for index, item in enumerate(request.expectations)
    )
    checks.extend(
        AcceptanceCheckV1(
            expectation=item.expectation, path=("acceptance_requirements", index, "expectation"), origin=item.origin
        )
        for index, item in enumerate(request.acceptance_requirements)
    )
    readbacks = _readbacks(request, entries, (canonical_document, *(step for _, step in included)))
    spec = AcceptanceSpecV1(products=spec.products, relationships=tuple(relationships), readbacks=readbacks)
    for check in checks:
        validate_acceptance_check(spec, check)
    # Distinct origins remain visible, even when the same fact is required twice.
    unique = {(expectation_identity(check.expectation), check.origin): check for check in checks}
    return AcceptanceSpecV1(
        products=spec.products,
        relationships=spec.relationships,
        readbacks=spec.readbacks,
        checks=tuple(unique.values()),
        declared_rows=_declared_rows(entries, counts, readbacks),
    )


def _declared_rows(
    entries: tuple[_Product, ...], counts: dict[str, int], readbacks: tuple[AcceptanceReadbackV1, ...]
) -> int | None:
    """An upper bound of the rows of all products, kept apart from ``counts`` because a source read can stop early:
    its literal count bounds it, a memstore readback without one reads its literal producer, and a source-free child
    multiplies its parent's bound. None when one product has no such bound (a script or range count, a file source
    without count)."""
    producers = {item.consumer: item.producer for item in readbacks}
    rows = dict(counts)
    for entry in entries:  # a parent precedes its children
        name = entry.product.name
        if name in rows:
            continue
        if entry.node.properties.get("source") is None:
            per_invocation = entry.count
        else:
            per_invocation = entry.product.count_per_invocation
            if per_invocation is None and name in producers:
                per_invocation = counts.get(producers[name])
        parent_rows = 1 if entry.parent is None else rows.get(entry.parent)
        if per_invocation is None or parent_rows is None:
            return None
        rows[name] = parent_rows * per_invocation
    return sum(rows.values()) if len(rows) == len(entries) else None


def _derive_field(
    field: DmJsonNodeV1,
    subject: ProductRowsSubject,
    path: tuple[str | int, ...],
    derive: Callable[[ExpectationIntent, tuple[str | int, ...]], None],
) -> None:
    if field.properties.get("condition") is not None or field.properties.get("converter") is not None:
        return
    name = _name(field, path)
    values = field.properties.get("values")
    if isinstance(values, str):
        try:
            literal = parse_literal_values(values)
        except (ValueError, SyntaxError):
            _reject(
                "Allowed values are not valid CE literal values.",
                path + ("properties", "values"),
                remediation=(
                    "Write values as quoted Python literals, for example values=\"'A', 'B'\" or values=\"[1, 2]\"."
                ),
            )
            return
        allowed: tuple[JsonValue, ...]
        if literal is None:
            allowed = (None,)
        elif isinstance(literal, list | tuple | str | bytes | set | dict):
            try:
                if isinstance(literal, dict) and not field.properties.get("unique"):
                    # Random choice indexes mappings; unique mode iterates their keys.
                    selected = tuple(literal[index] for index in range(len(literal)))
                else:
                    selected = tuple(literal)
                allowed = TypeAdapter(tuple[JsonValue, ...]).validate_python(selected, strict=True)
                if isinstance(literal, set):
                    allowed = tuple(sorted(allowed, key=lambda value: repr(value)))
            except (ValidationError, KeyError):
                _reject("Value vocabulary contains unsupported acceptance values.", path + ("properties", "values"))
                return
        else:
            _reject("Value vocabulary is not an indexable CE sequence.", path + ("properties", "values"))
            return
        if not allowed:
            _reject("Value vocabulary must not be empty.", path + ("properties", "values"))
        derive(AllowedValuesExpectation(subject=subject, field=name, values=allowed), path)
    minimum, maximum = field.properties.get("min"), field.properties.get("max")
    if (
        field.properties.get("type") in {"int", "float", "double", "decimal", "long"}
        and minimum is not None
        and maximum is not None
    ):
        try:
            lower, upper = Decimal(str(minimum)), Decimal(str(maximum))
        except InvalidOperation:
            _reject("Numeric range bounds must be finite decimal values.", path + ("properties",))
            return
        if not lower.is_finite():
            _reject("The lower range bound must be finite.", path + ("properties", "min"))
        if not upper.is_finite():
            _reject("The upper range bound must be finite.", path + ("properties", "max"))
        if lower > upper:
            _reject("The upper range bound must be at least the lower bound.", path + ("properties", "max"))
        derive(RangeExpectation(subject=subject, field=name, minimum=lower, maximum=upper), path)


def _readbacks(
    request: BuildRequestV5, entries: tuple[_Product, ...], documents: tuple[DmJsonDocumentV1, ...]
) -> tuple[AcceptanceReadbackV1, ...]:
    stores = {
        identifier
        for document in documents
        for node in document.root.children
        if node.kind == "memstore"
        if isinstance(identifier := node.properties.get("id"), str)
    }
    result = []
    producers_read: set[tuple[str, str]] = set()
    for consumer in entries:
        source = consumer.node.properties.get("source")
        if source not in stores:
            continue
        entity = consumer.node.properties.get(
            "source_entity", consumer.node.properties.get("type", consumer.product.name)
        )
        producers = [
            entry
            for entry in entries
            if _memstore_entity(entry.node, _name(entry.node, entry.path)) == entity
            and source in {item.strip() for item in str(entry.node.properties.get("target", "")).split(",")}
        ]
        if not producers:
            _reject(
                "No product writes the memstore entity that this source reads.",
                consumer.path,
                "Write the entity with a generate that targets this memstore. A product writes the entity named by "
                "targetEntity, else its own name; type and sourceEntity name only the entity that a source reads.",
            )
        if len(producers) > 1:
            _reject(
                "More than one product writes the memstore entity that this source reads.",
                consumer.path,
                "Give each writer its own entity. A product writes the entity named by targetEntity, else its own "
                "name; type and sourceEntity name only the entity that a source reads.",
            )
        producer = producers[0]
        if isinstance(source, str):
            producers_read.add((producer.product.name, source))
        for index, field in enumerate(consumer.node.children):
            name = field.properties.get("name")
            if isinstance(name, str) and name in producer.product.fields:
                script = field.properties.get("script")
                if not isinstance(script, str) or not references_current_scope_field(script, name):
                    _reject(
                        "A same-name memstore readback field must read its current source field.",
                        consumer.path + ("children", index),
                    )
        identifiers = {
            role.field
            for role in request.product_roles
            if role.product == producer.product.name
            and role.list_field is None
            and isinstance(role.role, IdentifierRole)
        }
        named = [
            role
            for role in request.product_roles
            if role.product == consumer.product.name
            and role.list_field is None
            and isinstance(role.role, ForeignKeyRole)
            and role.role.parent_product == producer.product.name
        ]
        candidates = [
            role for role in named if isinstance(role.role, ForeignKeyRole) and role.role.parent_field in identifiers
        ]
        if len(identifiers) != 1 or len(candidates) != 1:
            if len(identifiers) > 1:
                remediation = (
                    "Memstore readback checks one identifier role per producer: declare only the identifier that the "
                    "consumer's foreign key names, and express any other uniqueness as a unique expectation."
                )
            elif not identifiers:
                remediation = (
                    'Add the producer identifier role: {"product": "<producer>", "field": "<key>", "role": {"kind": '
                    '"identifier"}}.'
                    if named
                    else 'Add two product_roles entries: {"product": "<producer>", "field": "<key>", "role": {"kind": '
                    '"identifier"}} and {"product": "<consumer>", "field": "<field holding the key>", "role": {"kind": '
                    '"foreign_key", "parent_product": "<producer>", "parent_field": "<key>"}}.'
                )
            elif not candidates:
                remediation = (
                    "Add the consumer foreign-key role, or point an existing one at the producer's identifier field: "
                    '{"product": "<consumer>", "field": "<field holding the key>", '
                    '"role": {"kind": "foreign_key", "parent_product": "<producer>", "parent_field": "<key>"}}.'
                )
            else:
                remediation = (
                    "More than one foreign-key role on the consumer names this producer: keep only the one that reads "
                    "the memstore back."
                )
            _reject(
                "Memstore completeness requires one producer identifier role "
                "and one matching consumer foreign-key role.",
                consumer.path,
                remediation=remediation,
            )
        result.append(
            AcceptanceReadbackV1(
                producer=producer.product.name,
                consumer=consumer.product.name,
                producer_field=next(iter(identifiers)),
                consumer_field=candidates[0].field,
                path=consumer.path,
            )
        )
    for producer in entries:
        target = producer.node.properties.get("target")
        if not isinstance(target, str):
            continue
        for store in (item.strip() for item in target.split(",")):
            if store in stores and (producer.product.name, store) not in producers_read:
                _reject(
                    "A memstore target requires a declared consumer readback.",
                    producer.path + ("properties", "target"),
                    remediation=(
                        "Read the product back in a later generate (source=<memstore id>, type=<this product>) and "
                        "declare its identifier/foreign-key role pair; a product nothing reads back needs a file "
                        "target instead of the memstore."
                    ),
                )
    return tuple(result)
