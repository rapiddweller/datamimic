# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Pure AuthoringSpecV1 to runtime-DSL compiler.

The compiler owns translation and the intent-derived compile plan.  It performs
no I/O and invokes neither linting nor execution.  Every produced element is
validated against the live runtime registry before serialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from xml.etree.ElementTree import Element
from xml.sax.saxutils import quoteattr

from pydantic import ValidationError

from datamimic_ce._compat import assert_never
from datamimic_ce.authoring.contracts import (
    AllowedValuesAcceptancePlan,
    CompilePlan,
    DerivedAcceptancePlan,
    ExactCountAcceptancePlan,
    FieldPlan,
    FieldRolePlan,
    FileSourceBindingPlan,
    FileTargetBindingPlan,
    ForeignKeyAcceptancePlan,
    ForeignKeyRolePlan,
    GeneratedProductCompilePlan,
    IdentifierRolePlan,
    LeafFieldPlan,
    MemstoreRelationshipPlan,
    MemstoreSourceBindingPlan,
    MemstoreTargetBindingPlan,
    NestedListFieldPlan,
    NestedRelationshipPlan,
    PerParentCountAcceptancePlan,
    ProductCompilePlan,
    RangeAcceptancePlan,
    RelationshipPlan,
    SourceBindingPlan,
    SourceProductCompilePlan,
    TargetBindingPlan,
    TimeSeriesProductCompilePlan,
    TimestampRolePlan,
    UniqueAcceptancePlan,
    UnresolvedCompileFact,
    ValueRolePlan,
)
from datamimic_ce.authoring.schema import build_schema_index
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    ConstantField,
    DecimalRangeField,
    FieldIntentUnion,
    FileExportTarget,
    FileSource,
    ForeignKeyRole,
    GeneratedProduct,
    IdentifierRole,
    IncrementField,
    IntegerRangeField,
    MemstoreSource,
    MemstoreTarget,
    NestedGeneratedProduct,
    NestedListField,
    PatternField,
    PersonEmailField,
    PersonNameField,
    ProductIntentUnion,
    ScriptField,
    SourceProduct,
    StringLengthField,
    TimeSeriesProduct,
    TimestampRole,
    ValueRole,
    ValuesField,
    WeightedField,
)
from datamimic_ce.utils.timeseries import TimeSeriesConfig


class CompileError(ValueError):
    """Raised when valid business intent cannot map safely to runtime DSL."""


@dataclass(frozen=True)
class CompileResult:
    """Pure compiler output."""

    xml: str
    plan: CompilePlan


_PERSON_ENTITY_BASE = "_ent_person"


def _entity_variable(depth: int) -> str:
    return _PERSON_ENTITY_BASE if depth == 0 else f"{_PERSON_ENTITY_BASE}_{depth}"


def _uses_person(fields: tuple[FieldIntentUnion, ...]) -> bool:
    return any(isinstance(field, PersonNameField | PersonEmailField) for field in fields)


def _stringify_number(value: Decimal | int) -> str:
    return str(value)


def _literal_collection(values: tuple[object, ...]) -> str:
    """Serialize for the runtime's ``ast.literal_eval`` collection parser."""

    # ``repr(tuple(...))`` is Python's canonical literal encoder for the exact
    # grammar consumed by KeyVariableTask. It preserves singleton collection
    # shape and escapes quotes, backslashes and XML-illegal control characters.
    return repr(tuple(values))


def _field_element(field: FieldIntentUnion, *, depth: int) -> Element:
    attributes = {"name": field.name}
    if isinstance(field, IncrementField):
        attributes["generator"] = "IncrementGenerator"
        return Element("key", attributes)
    if isinstance(field, PersonNameField):
        attributes["script"] = f"{_entity_variable(depth)}.name"
        return Element("key", attributes)
    if isinstance(field, PersonEmailField):
        attributes["script"] = f"{_entity_variable(depth)}.email"
        return Element("key", attributes)
    if isinstance(field, IntegerRangeField | DecimalRangeField | StringLengthField):
        return _range_field_element(field, attributes)
    if isinstance(field, ValuesField | WeightedField | PatternField | ConstantField | ScriptField):
        return _literal_field_element(field, attributes)
    if isinstance(field, NestedListField):
        return _nested_list_element(field, attributes, depth)
    raise CompileError(f"unsupported field intent kind {field.kind!r}")


def _range_field_element(
    field: IntegerRangeField | DecimalRangeField | StringLengthField,
    attributes: dict[str, str],
) -> Element:
    if isinstance(field, IntegerRangeField):
        attributes.update({"type": "int", "min": str(field.minimum), "max": str(field.maximum)})
        if field.unique:
            attributes["distribution"] = "shuffle"
    elif isinstance(field, DecimalRangeField):
        attributes.update(
            {
                "type": "decimal",
                "min": _stringify_number(field.minimum),
                "max": _stringify_number(field.maximum),
            }
        )
    else:
        attributes.update(
            {
                "type": "string",
                "minLength": str(field.minimum),
                "maxLength": str(field.maximum),
            }
        )
    return Element("key", attributes)


def _literal_field_element(
    field: ValuesField | WeightedField | PatternField | ConstantField | ScriptField,
    attributes: dict[str, str],
) -> Element:
    if isinstance(field, ValuesField):
        attributes["values"] = _literal_collection(field.values)
    elif isinstance(field, WeightedField):
        attributes["values"] = _literal_collection(field.values)
        attributes["weights"] = _literal_collection(field.weights)
    elif isinstance(field, PatternField):
        attributes["pattern"] = field.pattern
    elif isinstance(field, ConstantField):
        attributes["constant"] = field.value
    else:
        attributes["script"] = field.script
    return Element("key", attributes)


def _nested_list_element(
    field: NestedListField,
    attributes: dict[str, str],
    depth: int,
) -> Element:
    attributes.update(
        {
            "type": "list",
            "minCount": str(field.minimum_count),
            "maxCount": str(field.maximum_count),
        }
    )
    nested = Element("nestedKey", attributes)
    nested_depth = depth + 1
    if _uses_person(field.fields):
        nested.append(
            Element(
                "variable",
                {"name": _entity_variable(nested_depth), "entity": "Person"},
            )
        )
    for child in field.fields:
        nested.append(_field_element(child, depth=nested_depth))
    return nested


def _target_attributes(product: ProductIntentUnion | NestedGeneratedProduct) -> dict[str, str]:
    target_names: list[str] = []
    export_uri: str | None = None
    for target in product.targets:
        if isinstance(target, FileExportTarget):
            target_names.append(target.format)
            export_uri = export_uri or target.export_uri
        elif isinstance(target, MemstoreTarget):
            target_names.append(target.id)
    result: dict[str, str] = {}
    if target_names:
        result["target"] = ",".join(target_names)
    if export_uri is not None:
        result["exportUri"] = export_uri
    return result


def _generate_element(
    product: ProductIntentUnion | NestedGeneratedProduct,
    *,
    depth: int,
) -> Element:
    attributes = _product_attributes(product)
    attributes.update(_target_attributes(product))
    element = Element("generate", attributes)
    _append_product_fields(element, product, depth)
    _append_generated_children(element, product, depth)
    return element


def _product_attributes(
    product: ProductIntentUnion | NestedGeneratedProduct,
) -> dict[str, str]:
    attributes = {"name": product.name}
    if isinstance(product, GeneratedProduct | NestedGeneratedProduct):
        attributes["count"] = str(product.count)
    elif isinstance(product, SourceProduct):
        attributes.update(_source_product_attributes(product))
    else:
        attributes.update(
            {
                "count": str(product.series_count),
                "start": product.window.start,
                "end": product.window.end,
                "interval": product.window.interval,
            }
        )
    return attributes


def _source_product_attributes(product: SourceProduct) -> dict[str, str]:
    source = product.source
    attributes: dict[str, str] = {}
    if isinstance(source, FileSource):
        attributes["source"] = source.path
        if source.separator is not None:
            attributes["separator"] = source.separator
    else:
        attributes["source"] = source.id
        if source.product is not None:
            attributes["type"] = source.product
    attributes["distribution"] = source.distribution
    return attributes


def _append_product_fields(
    element: Element,
    product: ProductIntentUnion | NestedGeneratedProduct,
    depth: int,
) -> None:
    if _uses_person(product.fields):
        element.append(Element("variable", {"name": _entity_variable(depth), "entity": "Person"}))
    for field in product.fields:
        element.append(_field_element(field, depth=depth))


def _append_generated_children(
    element: Element,
    product: ProductIntentUnion | NestedGeneratedProduct,
    depth: int,
) -> None:
    if isinstance(product, GeneratedProduct):
        for child in product.children:
            element.append(_generate_element(child, depth=depth + 1))


def _all_products(spec: AuthoringSpecV1) -> list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]]:
    products: list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]] = []
    for product in spec.products:
        products.append((product, None))
        if isinstance(product, GeneratedProduct):
            products.extend((child, product.name) for child in product.children)
    return products


def _memstore_ids(spec: AuthoringSpecV1) -> set[str]:
    result: set[str] = set()
    for product, _parent in _all_products(spec):
        for target in product.targets:
            if isinstance(target, MemstoreTarget):
                result.add(target.id)
        if isinstance(product, SourceProduct) and isinstance(product.source, MemstoreSource):
            result.add(product.source.id)
    return result


def _validate_registry_tree(element: Element, parent: Element | None = None) -> None:
    index = build_schema_index()
    schema = index.get(element.tag)
    if schema is None:
        raise CompileError(f"runtime registry does not define <{element.tag}>")
    if parent is not None:
        parent_schema = index.get(parent.tag)
        if parent_schema is None or (
            parent_schema.allowed_children is not None and element.tag not in parent_schema.allowed_children
        ):
            raise CompileError(f"runtime registry does not allow <{element.tag}> inside <{parent.tag}>")
    if not schema.open_attrs:
        unknown = sorted(set(element.attrib) - set(schema.attributes))
        if unknown:
            raise CompileError(
                f"runtime registry does not define attribute(s) on <{element.tag}>: {', '.join(unknown)}"
            )
    if schema.model is not None:
        try:
            schema.model.model_validate(element.attrib)
        except ValidationError as error:
            first = error.errors(include_url=False)[0]
            raise CompileError(f"runtime model rejected <{element.tag}>: {first['msg']}") from error
    for child in element:
        _validate_registry_tree(child, element)


def _serialize_element(element: Element, depth: int = 0) -> list[str]:
    indent = "    " * depth
    attributes = "".join(f" {name}={quoteattr(value)}" for name, value in element.attrib.items())
    if len(element) == 0:
        return [f"{indent}<{element.tag}{attributes}/>"]
    lines = [f"{indent}<{element.tag}{attributes}>"]
    for child in element:
        lines.extend(_serialize_element(child, depth + 1))
    lines.append(f"{indent}</{element.tag}>")
    return lines


def _producer_for_source(
    source: MemstoreSource,
    products: list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]],
) -> ProductIntentUnion | NestedGeneratedProduct:
    candidates = [
        product
        for product, _parent in products
        if any(isinstance(target, MemstoreTarget) and target.id == source.id for target in product.targets)
    ]
    if source.product is not None:
        candidates = [product for product in candidates if product.name == source.product]
    if len(candidates) != 1:
        detail = "none" if not candidates else ", ".join(product.name for product in candidates)
        raise CompileError(
            f"memstore source '{source.id}' must resolve to exactly one in-spec producer; resolved: {detail}"
        )
    return candidates[0]


def _static_cardinalities(
    spec: AuthoringSpecV1,
) -> tuple[
    dict[str, int | None],
    list[RelationshipPlan],
    list[UnresolvedCompileFact],
]:
    products = _all_products(spec)
    counts, relationships, unresolved = _direct_cardinalities(products)
    _resolve_memstore_cardinalities(products, counts, relationships, unresolved)
    return counts, relationships, unresolved


def _direct_cardinalities(
    products: list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]],
) -> tuple[
    dict[str, int | None],
    list[RelationshipPlan],
    list[UnresolvedCompileFact],
]:
    counts: dict[str, int | None] = {}
    relationships: list[RelationshipPlan] = []
    unresolved: list[UnresolvedCompileFact] = []
    for product, parent in products:
        _register_direct_cardinality(product, parent, counts, relationships, unresolved)
    return counts, relationships, unresolved


def _register_direct_cardinality(
    product: ProductIntentUnion | NestedGeneratedProduct,
    parent: str | None,
    counts: dict[str, int | None],
    relationships: list[RelationshipPlan],
    unresolved: list[UnresolvedCompileFact],
) -> None:
    if isinstance(product, GeneratedProduct | NestedGeneratedProduct):
        count: int | None = int(product.count)
        if parent is not None:
            parent_count = counts.get(parent)
            count = parent_count * int(product.count) if parent_count is not None else None
            relationships.append(NestedRelationshipPlan(parent=parent, child=product.name))
        counts[product.name] = count
    elif isinstance(product, TimeSeriesProduct):
        counts[product.name] = _time_series_cardinality(product)
    elif isinstance(product.source, FileSource):
        counts[product.name] = None
        unresolved.append(
            UnresolvedCompileFact(
                product=product.name,
                aspect="cardinality",
                reason="file source length requires I/O and is intentionally unknown at compile time",
            )
        )


def _time_series_cardinality(product: TimeSeriesProduct) -> int:
    try:
        window = TimeSeriesConfig.parse(
            product.window.start,
            product.window.end,
            product.window.interval,
        )
    except ValueError as error:
        raise CompileError(str(error)) from error
    return int(product.series_count) * window.ticks_per_series


def _memstore_source_products(
    products: list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]],
) -> list[SourceProduct]:
    return [
        product
        for product, _parent in products
        if isinstance(product, SourceProduct) and isinstance(product.source, MemstoreSource)
    ]


def _resolve_memstore_cardinalities(
    products: list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]],
    counts: dict[str, int | None],
    relationships: list[RelationshipPlan],
    unresolved: list[UnresolvedCompileFact],
) -> None:
    pending = _memstore_source_products(products)
    while pending:
        progressed = False
        for product in list(pending):
            if _resolve_memstore_cardinality(product, products, counts, relationships, unresolved):
                pending.remove(product)
                progressed = True
        if not progressed:
            cycle = ", ".join(product.name for product in pending)
            raise CompileError(f"cyclic or unresolved memstore source chain: {cycle}")


def _resolve_memstore_cardinality(
    product: SourceProduct,
    products: list[tuple[ProductIntentUnion | NestedGeneratedProduct, str | None]],
    counts: dict[str, int | None],
    relationships: list[RelationshipPlan],
    unresolved: list[UnresolvedCompileFact],
) -> bool:
    source = product.source
    if not isinstance(source, MemstoreSource):
        raise CompileError(f"internal source classification failed for '{product.name}'")
    producer = _producer_for_source(source, products)
    if producer.name not in counts:
        return False
    counts[product.name] = counts[producer.name]
    relationships.append(
        MemstoreRelationshipPlan(
            parent=producer.name,
            child=product.name,
            source_id=source.id,
        )
    )
    if counts[product.name] is None:
        unresolved.append(
            UnresolvedCompileFact(
                product=product.name,
                aspect="cardinality",
                reason=f"producer '{producer.name}' has unknown cardinality",
            )
        )
    return True


def _field_plan(field: FieldIntentUnion) -> FieldPlan:
    roles: list[FieldRolePlan] = []
    for role in field.roles:
        if isinstance(role, IdentifierRole):
            roles.append(IdentifierRolePlan())
        elif isinstance(role, ForeignKeyRole):
            roles.append(
                ForeignKeyRolePlan(
                    parent_product=role.parent_product,
                    parent_field=role.parent_field,
                )
            )
        elif isinstance(role, TimestampRole):
            roles.append(TimestampRolePlan())
        elif isinstance(role, ValueRole):
            roles.append(ValueRolePlan())
    if isinstance(field, NestedListField):
        return NestedListFieldPlan(
            name=field.name,
            roles=roles,
            minimum_count=field.minimum_count,
            maximum_count=field.maximum_count,
        )
    return LeafFieldPlan(name=field.name, kind=field.kind, roles=roles)


def _source_plan(product: SourceProduct) -> SourceBindingPlan:
    if isinstance(product.source, FileSource):
        return FileSourceBindingPlan(
            path=product.source.path,
            separator=product.source.separator,
            distribution=product.source.distribution,
        )
    if isinstance(product.source, MemstoreSource):
        return MemstoreSourceBindingPlan(
            id=product.source.id,
            product=product.source.product,
            distribution=product.source.distribution,
        )
    assert_never(product.source)


def _target_plans(
    product: ProductIntentUnion | NestedGeneratedProduct,
) -> list[TargetBindingPlan]:
    plans: list[TargetBindingPlan] = []
    for target in product.targets:
        if isinstance(target, FileExportTarget):
            plans.append(
                FileTargetBindingPlan(
                    format=target.format,
                    export_uri=target.export_uri,
                )
            )
        else:
            plans.append(MemstoreTargetBindingPlan(id=target.id))
    return plans


def _derived_field_acceptance(
    product: ProductIntentUnion | NestedGeneratedProduct,
) -> list[DerivedAcceptancePlan]:
    result: list[DerivedAcceptancePlan] = []
    unique_fields: set[str] = set()
    for field in product.fields:
        field_acceptance, field_is_unique = _derived_value_acceptance(product.name, field)
        result.extend(field_acceptance)
        if field_is_unique:
            unique_fields.add(field.name)
        result.extend(_derived_role_acceptance(product.name, field, unique_fields))
    return result


def _derived_value_acceptance(
    product_name: str,
    field: FieldIntentUnion,
) -> tuple[list[DerivedAcceptancePlan], bool]:
    if isinstance(field, IntegerRangeField):
        result: list[DerivedAcceptancePlan] = [
            RangeAcceptancePlan(
                product=product_name,
                field=field.name,
                minimum=str(field.minimum),
                maximum=str(field.maximum),
            )
        ]
        if field.unique:
            result.append(UniqueAcceptancePlan(product=product_name, field=field.name))
        return result, field.unique
    if isinstance(field, DecimalRangeField):
        return [
            RangeAcceptancePlan(
                product=product_name,
                field=field.name,
                minimum=str(field.minimum),
                maximum=str(field.maximum),
            )
        ], False
    if isinstance(field, ValuesField | WeightedField):
        return [
            AllowedValuesAcceptancePlan(
                product=product_name,
                field=field.name,
                allowed_values=list(field.values),
            )
        ], False
    return [], False


def _derived_role_acceptance(
    product_name: str,
    field: FieldIntentUnion,
    unique_fields: set[str],
) -> list[DerivedAcceptancePlan]:
    result: list[DerivedAcceptancePlan] = []
    for role in field.roles:
        if isinstance(role, IdentifierRole) and field.name not in unique_fields:
            unique_fields.add(field.name)
            result.append(UniqueAcceptancePlan(product=product_name, field=field.name))
        if isinstance(role, ForeignKeyRole):
            result.append(
                ForeignKeyAcceptancePlan(
                    product=product_name,
                    parent_product=role.parent_product,
                    parent_field=role.parent_field,
                    child_field=field.name,
                )
            )
    return result


def _compile_plan(spec: AuthoringSpecV1) -> CompilePlan:
    all_products = _all_products(spec)
    counts, relationships, unresolved = _static_cardinalities(spec)
    product_plans: list[ProductCompilePlan] = []
    acceptance: list[DerivedAcceptancePlan] = []
    for product, parent in all_products:
        per_parent = int(product.count) if isinstance(product, NestedGeneratedProduct) else None
        fields = [_field_plan(field) for field in product.fields]
        targets = _target_plans(product)
        product_plans.append(
            _product_compile_plan(
                product,
                parent=parent,
                per_parent=per_parent,
                static_count=counts[product.name],
                fields=fields,
                targets=targets,
            )
        )
        acceptance.extend(
            _derived_count_acceptance(
                product.name,
                parent=parent,
                per_parent=per_parent,
                static_count=counts[product.name],
            )
        )
        acceptance.extend(_derived_field_acceptance(product))
        _validate_unique_capacities(product, counts[product.name])
    return CompilePlan(
        products=product_plans,
        relationships=relationships,
        unresolved=unresolved,
        derived_acceptance=acceptance,
    )


def _product_compile_plan(
    product: ProductIntentUnion | NestedGeneratedProduct,
    *,
    parent: str | None,
    per_parent: int | None,
    static_count: int | None,
    fields: list[FieldPlan],
    targets: list[TargetBindingPlan],
) -> ProductCompilePlan:
    if isinstance(product, GeneratedProduct | NestedGeneratedProduct):
        if static_count is None:
            raise CompileError(f"generated product '{product.name}' has unknown cardinality")
        children = [child.name for child in product.children] if isinstance(product, GeneratedProduct) else []
        return GeneratedProductCompilePlan(
            name=product.name,
            fields=fields,
            targets=targets,
            parent=parent,
            children=children,
            static_count=static_count,
            count_per_parent=per_parent,
        )
    if isinstance(product, SourceProduct):
        source = _source_plan(product)
        return SourceProductCompilePlan(
            name=product.name,
            fields=fields,
            targets=targets,
            static_count=static_count,
            source=source,
        )
    if static_count is None:
        raise CompileError(f"time-series product '{product.name}' has unknown cardinality")
    return TimeSeriesProductCompilePlan(
        name=product.name,
        fields=fields,
        targets=targets,
        static_count=static_count,
        series_count=product.series_count,
    )


def _derived_count_acceptance(
    product_name: str,
    *,
    parent: str | None,
    per_parent: int | None,
    static_count: int | None,
) -> list[DerivedAcceptancePlan]:
    result: list[DerivedAcceptancePlan] = []
    if static_count is not None:
        result.append(ExactCountAcceptancePlan(product=product_name, exact_count=static_count))
    if parent is not None and per_parent is not None:
        result.append(
            PerParentCountAcceptancePlan(
                product=product_name,
                parent_product=parent,
                count_per_parent=per_parent,
            )
        )
    return result


def _validate_unique_capacities(
    product: ProductIntentUnion | NestedGeneratedProduct,
    required_count: int | None,
) -> None:
    for field in product.fields:
        if not isinstance(field, IntegerRangeField) or not field.unique:
            continue
        if required_count is None:
            raise CompileError(
                f"field '{field.name}' in product '{product.name}' uses unique=true but "
                "cardinality is not statically known"
            )
        capacity = field.maximum - field.minimum + 1
        if capacity < required_count:
            raise CompileError(
                f"field '{field.name}' in product '{product.name}' has only {capacity} "
                f"possible values under unique=true but requires {required_count}"
            )


def compile_authoring_spec(spec: AuthoringSpecV1) -> CompileResult:
    """Compile validated business intent into canonical XML and a static plan."""

    root_attributes = {"rngSeed": str(spec.seed)} if spec.seed is not None else {}
    root = Element("setup", root_attributes)
    for memstore_id in sorted(_memstore_ids(spec)):
        root.append(Element("memstore", {"id": memstore_id}))
    for product in spec.products:
        root.append(_generate_element(product, depth=0))
    _validate_registry_tree(root)
    plan = _compile_plan(spec)
    return CompileResult(xml="\n".join(_serialize_element(root)), plan=plan)


__all__ = ["CompileError", "CompileResult", "compile_authoring_spec"]
