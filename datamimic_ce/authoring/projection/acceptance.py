# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Bind complete CE descriptor facts and transaction requirements to acceptance."""

from __future__ import annotations

import ast
import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import NoReturn

from pydantic import JsonValue, TypeAdapter, ValidationError

from datamimic_ce.authoring.domain.acceptance_contract import (
    MEMSTORE_READBACK_ONCE,
    AcceptanceCheckV1,
    AcceptanceJoinV1,
    AcceptanceListV1,
    AcceptanceProductV1,
    AcceptanceProjectionError,
    AcceptanceReadbackV1,
    AcceptanceRelationshipV1,
    AcceptanceSpecV1,
    memstore_readback_once,
    validate_acceptance_check,
    validate_acceptance_subject,
)
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, DmJsonNodeV1, iter_dm_json_nodes
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
    DATA_TYPE_LIST,
    EL_ARRAY,
    EL_CONDITION,
    EL_DATABASE,
    EL_ELEMENT,
    EL_FIELD,
    EL_GENERATE,
    EL_ID,
    EL_KEY,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_VARIABLE,
    META_TARGET_ENTITY,
    META_TYPE,
    NAME_SEPARATOR,
    ExportOperation,
    GenerateStatement,
    TimeSeriesConfig,
    TimeSeriesConfigError,
    capture_product_name,
    column_names,
    parse_literal_values,
    source_file_format_for,
    split_targets,
)
from datamimic_ce.errors import GUIDANCE_LOOKUP_POINTER

# The DM JSON kinds of a scalar field: <id> keeps its kind in DM JSON because it marks a createTable primary key.
_KEY_KINDS = frozenset({EL_KEY, EL_ID})


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
    if node.kind == EL_CONDITION:
        # Branches are exclusive; retain duplicates within each branch.
        alternatives: Counter[str] = Counter()
        for branch in node.children:
            alternatives |= Counter(_fields(branch))
        return tuple(alternatives.elements())
    fields: list[str] = []
    for child in node.children:
        if child.kind == EL_GENERATE:
            continue
        name = child.properties.get("name")
        if child.kind in {*_KEY_KINDS, EL_NESTED_KEY, EL_ARRAY} and isinstance(name, str):
            fields.append(name)
        elif child.kind == EL_REFERENCE:
            mapped = tuple(item.properties.get("target") for item in child.children if item.kind == EL_FIELD)
            fields.extend(item for item in mapped if isinstance(item, str))
            if not mapped and isinstance(name, str):
                fields.append(name)
        elif child.kind not in {EL_VARIABLE, EL_ELEMENT}:
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
    target_entity = node.properties.get(META_TARGET_ENTITY)
    return GenerateStatement.memstore_entity(target_entity if isinstance(target_entity, str) else None, name)


def _target_entity(node: DmJsonNodeV1, name: str) -> str:
    """A database or MongoDB sink's entity; type takes part here, unlike a memstore write."""
    for attribute in (META_TARGET_ENTITY, META_TYPE):
        value = node.properties.get(attribute)
        if isinstance(value, str) and value:
            return value
    return name


def _products(document: DmJsonDocumentV1, included: tuple[tuple[str, DmJsonDocumentV1], ...]) -> tuple[_Product, ...]:
    declarations = {
        node.properties.get("id"): node.kind
        for node in document.root.children
        if node.kind in {EL_DATABASE, EL_MONGODB}
    }
    entries: list[_Product] = []

    def visit(node: DmJsonNodeV1, path: tuple[str | int, ...], parent: _Product | None) -> None:
        # A source-free clear or drop produces no rows: it is an operation, not a product to prove.
        target = node.properties.get("target")
        if node.kind == EL_GENERATE and not (isinstance(target, str) and names_statement_operation(target)):
            name = _name(node, path)
            runtime_name = NAME_SEPARATOR.join((parent.product.runtime_name, name)) if parent else name
            entity = _target_entity(node, name)
            targets = node.properties.get("target", "")
            sinks: list[DeclaredSinkIdentity] = []
            if isinstance(targets, str) and isinstance(entity, str):
                for part in split_targets(targets):
                    client, operation = ExportOperation.from_target(part) or (part, None)
                    # A delete removes rows from the client, so the client does not hold the captured rows.
                    if operation not in (None, ExportOperation.UPDATE, ExportOperation.UPSERT):
                        continue
                    family = declarations.get(client)
                    if family == EL_DATABASE:
                        sinks.append(DeclaredSinkIdentity(kind="database", environment=client, entity=entity))
                    elif family == EL_MONGODB:
                        sinks.append(DeclaredSinkIdentity(kind="mongodb", environment=client, entity=entity))
            lists = tuple(
                AcceptanceListV1(
                    name=_name(child, path),
                    fields=_fields(child),
                    count_per_row=_count(child, path + ("children", index)),
                )
                for index, child in enumerate(node.children)
                if child.kind == EL_NESTED_KEY and child.properties.get(META_TYPE) == DATA_TYPE_LIST
            )
            source = node.properties.get("source")
            fields = _fields(node)
            columns = node.properties.get("columns")
            if isinstance(columns, str):
                # columns= declares the source columns it emits; a key of the same name replaces the column.
                fields = (*(name for name in column_names(columns) if name not in fields), *fields)
            if len(fields) != len(set(fields)):
                _reject(
                    "Declared output fields must be unique for acceptance.",
                    path + ("children",),
                    remediation="Give each <key> of one product its own name. For a value that depends on a "
                    "condition, write one key with both cases: script=\"'A' if n == 1 else 'B'\".",
                )
            product = AcceptanceProductV1(
                name=name,
                runtime_name=runtime_name,
                capture_name=capture_product_name(runtime_name),
                count_per_invocation=_count_per_invocation(node),
                fields=fields,
                lists=lists,
                declared_sinks=tuple(sinks),
                reads_file_source=isinstance(source, str) and source_file_format_for(node.kind, source) is not None,
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
    by_name = {entry.product.name: entry for entry in entries}
    for entry in entries:
        name = entry.product.name
        subject = ProductRowsSubject(product=name)
        if entry.parent:
            parent_node = by_name[entry.parent].node
            parent_variables = {
                child.properties.get("name") for child in parent_node.children if child.kind == EL_VARIABLE
            }
            joins = tuple(
                AcceptanceJoinV1(child_field=_name(child, entry.path), parent_field=parent_field)
                for child in entry.node.children
                if child.kind in _KEY_KINDS
                if (parent_field := _parent_reference(child.properties.get("script"))) is not None
                # A <variable> of the parent is no output field, so it joins nothing; the run resolves it (#442 T1).
                if parent_field in by_name[entry.parent].product.fields or parent_field not in parent_variables
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
        primary_key = [child for child in entry.node.children if child.kind == EL_ID]
        # A createTable primary key must be unique. A unique expectation names one field, so a composite key (several
        # <id>) derives nothing: each of its fields alone may repeat.
        if entry.node.properties.get("create_table") is True and len(primary_key) == 1:
            derive(UniqueExpectation(subject=subject, field=_name(primary_key[0], entry.path)), entry.path)
        for index, field in enumerate(entry.node.children):
            if field.kind in _KEY_KINDS:
                _derive_field(field, subject, entry.path + ("children", index), derive)
            elif field.kind == EL_NESTED_KEY and field.properties.get(META_TYPE) == DATA_TYPE_LIST:
                list_name = _name(field, entry.path)
                list_subject = ProductRowsSubject(product=name, list_field=list_name)
                for inner_index, inner in enumerate(field.children):
                    if inner.kind in _KEY_KINDS:
                        _derive_field(
                            inner, list_subject, entry.path + ("children", index, "children", inner_index), derive
                        )
    for relationship in relationships:
        for join in relationship.joins:
            if join.parent_field not in by_name[relationship.parent_product].product.fields:
                _reject(
                    "Parent reference names an unknown field.",
                    by_name[relationship.child_product].path,
                    remediation="A child <key> script parent.<name> reads a <key>, a columns= column or a <variable> "
                    'of the parent. Declare a source column in the parent as <key name="region" '
                    'script="this.region"/>, or list it in columns=.',
                )
    spec = AcceptanceSpecV1(products=tuple(entry.product for entry in entries), relationships=tuple(relationships))
    explicit_joins: dict[tuple[str, str], tuple[AcceptanceJoinV1, ...]] = {}
    composite_identities: dict[str, tuple[str, ...]] = {}
    for index, declaration in enumerate(request.product_roles):
        path = ("product_roles", index)
        subject = ProductRowsSubject(product=declaration.product, list_field=declaration.list_field)
        validate_acceptance_subject(spec, subject, path, declaration.field)
        if isinstance(declaration.role, IdentifierRole):
            if declaration.role.additional_fields:
                fields = (declaration.field, *declaration.role.additional_fields)
                if declaration.list_field is not None or len(set(fields)) != len(fields):
                    _reject("A composite Memstore identity must name distinct top-level fields.", path)
                if declaration.product in composite_identities or _identifier_fields(request, declaration.product):
                    _reject("A composite Memstore identity must be the only top-level identifier on its product.", path)
                for field_index, field_name in enumerate(declaration.role.additional_fields):
                    validate_acceptance_subject(
                        spec, subject, path + ("role", "additional_fields", field_index), field_name
                    )
                composite_identities[declaration.product] = fields
                continue
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
                    _reject(
                        "A nested foreign-key role must copy the exact parent field using parent.field. "
                        f"The role makes '{declaration.product}.{declaration.field}' a key of "
                        f"'{role.parent_product}.{role.parent_field}', but the field is not exactly "
                        f'script="parent.{role.parent_field}": a computed value matches no parent row.',
                        path,
                        remediation=f'Set script="parent.{role.parent_field}" on the field. Remove the role only '
                        "when the field holds a derived value on purpose.",
                    )
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
    readbacks = _readbacks(request, entries, canonical_document, included, composite_identities)
    readback_producers = {readback.producer for readback in readbacks}
    for index, declaration in enumerate(request.product_roles):
        if (
            isinstance(declaration.role, IdentifierRole)
            and declaration.role.additional_fields
            and declaration.product not in readback_producers
        ):
            _reject(
                "A composite identifier requires a <generate source> Memstore readback.",
                ("product_roles", index),
            )
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


_KEY = "<key>"
_HOLDER = "<field holding the key>"


def _readback_roles(producer: str, consumer: str, key: str, holder: str) -> tuple[str, str]:
    """The product_roles pair of one readback; field and product names are structural, so the templates carry them."""
    producer_name, consumer_name = json.dumps(producer), json.dumps(consumer)
    key_name, holder_name = json.dumps(key), json.dumps(holder)
    return (
        f'{{"product": {producer_name}, "field": {key_name}, "role": {{"kind": "identifier"}}}}',
        f'{{"product": {consumer_name}, "field": {holder_name}, "role": {{"kind": "foreign_key", '
        f'"parent_product": {producer_name}, "parent_field": {key_name}}}}}',
    )


def _identifier_fields(request: BuildRequestV5, product: str) -> set[str]:
    return {
        role.field
        for role in request.product_roles
        if role.product == product
        and role.list_field is None
        and isinstance(role.role, IdentifierRole)
        and not role.role.additional_fields
    }


def _copied_fields(consumer: DmJsonNodeV1, producer_fields: tuple[str, ...]) -> dict[str, str]:
    """Each producer field that a consumer key copies unchanged (this.<field>), with the first such key."""
    copies: dict[str, str] = {}
    for child in consumer.children:
        name, script = child.properties.get("name"), child.properties.get("script")
        if child.kind in _KEY_KINDS and isinstance(name, str) and isinstance(script, str):
            for field in producer_fields:
                if field not in copies and is_exact_scope_field_reference(script, ScriptScope.CURRENT, field):
                    copies[field] = name
    return copies


def _unread_memstore_remediation(producer: _Product, store: str, identifiers: set[str]) -> str:
    """Agents write a memstore for a subset or a lookup; the first rejection names the route for each need."""
    name = producer.product.name
    copy = f"{name}_copy"
    key, holder = _KEY, _HOLDER
    if len(identifiers) == 1:
        (key,) = identifiers
        holder = key
    producer_role, consumer_role = _readback_roles(name, copy, key, holder)
    entity = _memstore_entity(producer.node, name)
    return (
        f'Nothing reads "{name}" from the memstore. To use its rows in a step, read them with '
        f'<variable name="rows" source="{store}" sourceEntity="{entity}" storage="data" distribution="ordered"/> '
        "inside the <generate> of that step. "
        f'{MEMSTORE_READBACK_ONCE} For that subset route, also remove target="{store}". A lookup in a data file: '
        f'remove the <memstore> and the generate that writes target="{store}". {GUIDANCE_LOOKUP_POINTER} '
        "A copy of every row: "
        f'after {name} add <generate name="{copy}" source="{store}" sourceEntity="{entity}" distribution="ordered" '
        f'target="ConsoleExporter"><key name="{key}" script="this.{key}"/></generate> and the '
        f"product_roles {producer_role} and {consumer_role}. "
        "Full project: datamimic authoring reference --topic examples --name memstore."
    )


def _role_pair_remediation(
    producer: _Product,
    consumer: _Product,
    store: str,
    identifiers: set[str],
    parent_fields: tuple[str, ...],
    several_foreign_keys: bool,
) -> str:
    """Name the fields Build can see in the descriptor; a subset readback can never pass, so it gets the nest route.

    The subset check runs first: no role can make a readback with fewer rows than its producer pass."""
    producer_name, consumer_name = producer.product.name, consumer.product.name
    consumer_count = _count_per_invocation(consumer.node)
    # One invocation's literal count: a nested producer read at or above it gets the role template (a missed route).
    if producer.count is not None and consumer_count is not None and consumer_count < producer.count:
        fields = (*sorted(identifiers), *producer.product.fields)
        example = fields[0] if fields else "id"
        return (
            f'"{consumer_name}" sets a count below the rows of "{producer_name}", so this readback cannot pass. '
            f'Move <generate name="{consumer_name}"> inside <generate name="{producer_name}">. Remove its '
            f'source="{store}" and sourceEntity, and remove "{store}" from the target of "{producer_name}" when '
            "nothing else reads it. Its keys then write parent.<field> where they now write this.<field>. "
            f"{memstore_readback_once(example)}"
        )
    if len(identifiers) > 1:
        return (
            "Memstore readback checks one identifier role per producer: declare only the identifier that the "
            "consumer's foreign key names, and express any other uniqueness as a unique expectation."
        )
    if several_foreign_keys:
        return (
            "More than one foreign-key role on the consumer names this producer: keep only the one that reads "
            "the memstore back."
        )
    copies = _copied_fields(consumer.node, producer.product.fields)
    key, holder = _KEY, _HOLDER
    if identifiers:
        (key,) = identifiers
        holder = copies.get(key, key)
    elif len(set(parent_fields)) == 1:
        key = parent_fields[0]
    elif copies:
        key = f"<{' or '.join(copies)}: the field that differs in every row>"
    producer_role, consumer_role = _readback_roles(producer_name, consumer_name, key, holder)
    if not identifiers:
        return (
            f"Add the producer identifier role: {producer_role}. {MEMSTORE_READBACK_ONCE}"
            if parent_fields
            else f"Add two product_roles entries: {producer_role} and {consumer_role}. {MEMSTORE_READBACK_ONCE}"
        )
    missing_key = ""
    if key in consumer.product.fields and key not in copies:
        # A second key of the same name would be rejected as a duplicate output field.
        missing_key = f' Set the script of key "{key}" in {consumer_name} to this.{key}.'
    elif key not in copies:
        missing_key = f' First add <key name="{key}" script="this.{key}"/> to {consumer_name}.'
    return (
        "Add the consumer foreign-key role, or point an existing one at the producer's identifier field: "
        f"{consumer_role}.{missing_key} {MEMSTORE_READBACK_ONCE}"
    )


def _read_entity(node: DmJsonNodeV1, name: object) -> object:
    """The entity that a memstore source reads, as the runtime resolves it: sourceEntity, else type, else the name."""
    return node.properties.get("source_entity", node.properties.get("type", name))


def _writer(entries: tuple[_Product, ...], entity: object, store: str, path: tuple[str | int, ...]) -> _Product:
    """The one product that writes ``entity`` into ``store``; an entity that no or two products write is rejected."""
    producers = [
        entry
        for entry in entries
        if _memstore_entity(entry.node, _name(entry.node, entry.path)) == entity
        and store in {item.strip() for item in str(entry.node.properties.get("target", "")).split(",")}
    ]
    if not producers:
        _reject(
            "No product writes the memstore entity that this source reads.",
            path,
            "Write the entity with a generate that targets this memstore. A product writes the entity named by "
            "targetEntity, else its own name; type and sourceEntity name only the entity that a source reads.",
        )
    if len(producers) > 1:
        _reject(
            "More than one product writes the memstore entity that this source reads.",
            path,
            "Give each writer its own entity. A product writes the entity named by targetEntity, else its own "
            "name; type and sourceEntity name only the entity that a source reads.",
        )
    return producers[0]


def _readback_joins(
    request: BuildRequestV5,
    producer: _Product,
    consumer: _Product,
    source: str,
    composite_fields: tuple[str, ...] | None,
) -> tuple[AcceptanceJoinV1, ...]:
    named = [
        AcceptanceJoinV1(parent_field=declaration.role.parent_field, child_field=declaration.field)
        for declaration in request.product_roles
        if declaration.product == consumer.product.name
        and declaration.list_field is None
        and isinstance(declaration.role, ForeignKeyRole)
        and declaration.role.parent_product == producer.product.name
    ]
    if composite_fields is not None:
        joins = [join for join in named if join.parent_field in composite_fields]
        by_parent = {join.parent_field: join for join in joins}
        if (
            len(joins) != len(composite_fields)
            or set(by_parent) != set(composite_fields)
            or len({join.child_field for join in joins}) != len(joins)
        ):
            _reject(
                "Memstore readback requires one distinct consumer foreign-key field per composite identity field.",
                consumer.path,
                remediation=f"Map each producer field to one consumer field: {', '.join(composite_fields)}.",
            )
        return tuple(by_parent[field] for field in composite_fields)

    identifiers = _identifier_fields(request, producer.product.name)
    candidates = tuple(join for join in named if join.parent_field in identifiers)
    if len(identifiers) != 1 or len(candidates) != 1:
        _reject(
            "Memstore completeness requires one producer identifier role and one matching consumer foreign-key role.",
            consumer.path,
            remediation=_role_pair_remediation(
                producer, consumer, source, identifiers, tuple(join.parent_field for join in named), len(candidates) > 1
            ),
        )
    return candidates


def _readbacks(
    request: BuildRequestV5,
    entries: tuple[_Product, ...],
    document: DmJsonDocumentV1,
    included: tuple[tuple[str, DmJsonDocumentV1], ...],
    composite_identities: dict[str, tuple[str, ...]],
) -> tuple[AcceptanceReadbackV1, ...]:
    documents = ((("document",), document), *((("include", uri), step) for uri, step in included))
    stores = {
        identifier
        for _, step in documents
        for node in step.root.children
        if node.kind == EL_MEMSTORE
        if isinstance(identifier := node.properties.get("id"), str)
    }
    result = []
    producers_read: set[tuple[str, str]] = set()
    for consumer in entries:
        source = consumer.node.properties.get("source")
        if not isinstance(source, str) or source not in stores:
            continue
        producer = _writer(entries, _read_entity(consumer.node, consumer.product.name), source, consumer.path)
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
        result.append(
            AcceptanceReadbackV1(
                producer=producer.product.name,
                consumer=consumer.product.name,
                joins=_readback_joins(
                    request, producer, consumer, source, composite_identities.get(producer.product.name)
                ),
                path=consumer.path,
            )
        )
    # A variable copies no rows into a product, so it needs no role pair; Build checks the store contents instead.
    for prefix, step in documents:
        for node, path in iter_dm_json_nodes(step):
            source = node.properties.get("source")
            if node.kind == EL_VARIABLE and isinstance(source, str) and source in stores:
                reader_path = (*prefix, *path[1:])
                producer = _writer(entries, _read_entity(node, node.properties.get("name")), source, reader_path)
                producers_read.add((producer.product.name, source))
    for producer in entries:
        target = producer.node.properties.get("target")
        if not isinstance(target, str):
            continue
        for store in (item.strip() for item in target.split(",")):
            if store in stores and (producer.product.name, store) not in producers_read:
                _reject(
                    "A memstore target requires a reader: a <generate source> readback or a <variable source> read.",
                    producer.path + ("properties", "target"),
                    remediation=_unread_memstore_remediation(
                        producer, store, _identifier_fields(request, producer.product.name)
                    ),
                )
    return tuple(result)
