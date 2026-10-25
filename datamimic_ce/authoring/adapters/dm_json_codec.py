# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""The sole model-registry-backed codec between agent DM JSON and DATAMIMIC XML."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy

from lxml import etree
from pydantic import JsonValue, TypeAdapter, ValidationError

from datamimic_ce.authoring.domain.dm_json import (
    DM_JSON_TRAVERSAL_COUNT,
    DM_JSON_TRAVERSAL_LIMIT,
    DmJsonCodecError,
    DmJsonCompilation,
    DmJsonContentV1,
    DmJsonDocumentV1,
    DmJsonNodeV1,
    DmJsonScalar,
)
from datamimic_ce.authoring.domain.script_semantics import names_statement_operation
from datamimic_ce.engine.dsl.api import (
    EXIST_COUNT,
    DTDForbiddenError,
    canonical_tag,
    check_constraints,
    check_is_digit_or_script,
    element_constraints,
    get_element_definition,
    list_element_tags,
    parse_xml_source,
    serialize_constraints,
)
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_COUNT, ATTR_MAX_COUNT, ATTR_SOURCE
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_GENERATE
from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import ElementContentMode, ElementContentModeKind


class CeDmJsonCodec:
    """Own registry validation, canonicalization, schema projection, and XML codec semantics."""

    def compile(self, document: DmJsonDocumentV1) -> DmJsonCompilation:
        canonical = _normalize_document(document)
        root = _compile_node(canonical.root, path=("root",))
        if canonical.root.comment is not None:
            root.addprevious(_xml_comment(canonical.root.comment, path=("root", "comment")))
        tree = root.getroottree()
        _indent_elements(root)
        serialized = etree.tostring(tree, encoding="unicode", pretty_print=True)
        if not isinstance(serialized, str):  # pragma: no cover - lxml contract
            raise TypeError("XML serializer did not return text")
        xml = serialized.strip()
        # WHY: XML attributes are textual, so its exact roundtrip is the one canonical
        # representation shared by build, read, and semantic hashing.
        return DmJsonCompilation(document=self.decompile(xml), xml=xml)

    def decompile(self, xml: str) -> DmJsonDocumentV1:
        try:
            tree = parse_xml_source(xml, preserve_comments=True, preserve_pis=True).getroottree()
        except DTDForbiddenError as error:
            raise DmJsonCodecError("DTD declarations are not supported", path=("xml",)) from error
        except (etree.XMLSyntaxError, UnicodeError) as error:
            raise DmJsonCodecError("Invalid XML syntax or encoding.", path=("xml",)) from error
        if tree.docinfo.doctype:
            raise DmJsonCodecError("DTD declarations are not supported", path=("xml",))
        root = tree.getroot()
        if not isinstance(root.tag, str):
            raise DmJsonCodecError("XML has no element root", path=("xml",))
        try:
            return _normalize_document(
                DmJsonDocumentV1(root=_decompile_node(root, path=("root",), comment=_root_comment(root)))
            )
        except (TypeError, ValueError, ValidationError) as error:
            if isinstance(error, DmJsonCodecError):
                raise
            raise DmJsonCodecError(
                "XML cannot be represented by the registered DM JSON contract.", path=("root",)
            ) from error

    def document_schema(self) -> dict[str, object]:
        return self.project_document_schema(DmJsonDocumentV1.model_json_schema())

    def project_document_schema(self, schema: Mapping[str, object]) -> dict[str, object]:
        return _project_dm_json_variants_into_schema(schema)


def _indent_elements(element: etree._Element, level: int = 0) -> None:
    # Preserve whitespace-only leaf bodies (echo), which etree.indent rewrites.
    if len(element):
        element.text = "\n" + "    " * (level + 1)
        for child in element:
            _indent_elements(child, level + 1)
            child.tail = "\n" + "    " * (level + 1)
        element[-1].tail = "\n" + "    " * level


def _normalize_document(document: DmJsonDocumentV1) -> DmJsonDocumentV1:
    return DmJsonDocumentV1(root=_normalize_node(document.root, path=("root",)))


def _normalize_node(node: DmJsonNodeV1, *, path: tuple[str | int, ...]) -> DmJsonNodeV1:
    tag = canonical_tag(node.kind)
    definition = get_element_definition(tag)
    if definition is None:
        raise DmJsonCodecError(f"unknown DATAMIMIC element kind {node.kind!r}", path=path + ("kind",))
    properties = _normalize_properties(tag, node.properties, path=path + ("properties",))
    children = tuple(
        _normalize_node(child, path=path + ("children", index)) for index, child in enumerate(node.children)
    )
    if definition.allowed_children is not None:
        for index, child in enumerate(children):
            if child.kind not in {canonical_tag(tag) for tag in definition.allowed_children}:
                raise DmJsonCodecError(
                    f"element {tag!r} does not allow child element {child.kind!r}",
                    path=path + ("children", index, "kind"),
                )
    if node.content is not None:
        allowed_modes = {mode.kind for mode in definition.content_modes}
        if node.content.kind not in allowed_modes:
            allowed = ", ".join(sorted(item.value for item in allowed_modes)) or "none"
            raise DmJsonCodecError(
                f"element {tag!r} does not support content mode {node.content.kind.value!r}; allowed: {allowed}",
                path=path + ("content",),
            )
    content_property_names = {attribute for mode in definition.content_modes for attribute in mode.required_attributes}
    duplicate_content = content_property_names.intersection(properties)
    if duplicate_content:
        raise DmJsonCodecError(
            f"element {tag!r} represents {', '.join(sorted(duplicate_content))} through content, not properties",
            path=path + ("properties",),
        )
    for index, child in enumerate(children):
        if child.kind in definition.singleton_children and any(
            previous.kind == child.kind for previous in children[:index]
        ):
            raise DmJsonCodecError(f"duplicate child container {child.kind!r}", path=path + ("children", index))
    attributes: dict[str, object] = dict(_compile_properties(tag, properties, path=path + ("properties",)))
    if node.content is not None:
        mode = next(item for item in definition.content_modes if item.kind == node.content.kind)
        for attribute in mode.required_attributes:
            attributes[attribute] = node.content.value
    constraints = element_constraints(node.kind)
    target = attributes.get("target")
    if isinstance(target, str) and names_statement_operation(target):
        constraints = tuple(constraint for constraint in constraints if constraint != EXIST_COUNT)  # runs once
    try:
        check_constraints(attributes, constraints)
    except ValueError as error:
        raise DmJsonCodecError(
            "Element properties violate registered DSL constraints.", path=path + ("properties",)
        ) from error
    return DmJsonNodeV1(
        kind=tag,
        properties=properties,
        content=node.content,
        comment=node.comment,
        children=children,
    )


def _property_aliases(tag: str) -> tuple[dict[str, str], tuple[str, ...]]:
    definition = get_element_definition(tag)
    if definition is None:  # pragma: no cover - normalized caller
        raise DmJsonCodecError(f"unknown DATAMIMIC element kind {tag!r}")
    aliases: dict[str, str] = {}
    field_order: list[str] = []
    for field_name, field in (definition.model.model_fields if definition.model is not None else {}).items():
        field_order.append(field_name)
        aliases[field_name] = field_name
        if isinstance(field.alias, str):
            aliases[field.alias] = field_name
    return aliases, tuple(field_order)


def is_source_driven_properties(tag: str, property_names: Mapping[str, object] | tuple[str, ...]) -> bool:
    """Recognize source-driven nodes through the registry-owned property aliases."""
    if tag != EL_GENERATE:
        return False
    aliases, _ = _property_aliases(tag)
    names = property_names if isinstance(property_names, tuple) else tuple(property_names)
    source_name = aliases.get(ATTR_SOURCE, ATTR_SOURCE)
    return any(aliases.get(name, name) == source_name for name in names)


def project_dm_json_property_name(tag: str, property_name: str, *, source_driven: bool) -> str:
    """Map one registry-backed XML/model property into canonical DM JSON vocabulary."""
    aliases, _ = _property_aliases(tag)
    canonical_name = aliases.get(property_name, property_name)
    if not source_driven or tag != EL_GENERATE:
        return canonical_name
    if canonical_name == aliases.get(ATTR_COUNT, ATTR_COUNT):
        return DM_JSON_TRAVERSAL_COUNT
    if canonical_name == aliases.get(ATTR_MAX_COUNT, ATTR_MAX_COUNT):
        return DM_JSON_TRAVERSAL_LIMIT
    return canonical_name


def _source_cardinality_property_names(tag: str) -> frozenset[str]:
    aliases, _ = _property_aliases(tag)
    return frozenset((aliases.get(ATTR_COUNT, ATTR_COUNT), aliases.get(ATTR_MAX_COUNT, ATTR_MAX_COUNT)))


def _normalize_properties(
    tag: str,
    properties: Mapping[str, DmJsonScalar],
    *,
    path: tuple[str | int, ...],
) -> dict[str, DmJsonScalar]:
    aliases, field_order = _property_aliases(tag)
    source_driven = is_source_driven_properties(tag, tuple(properties))
    normalized: dict[str, DmJsonScalar] = {}
    definition = get_element_definition(tag)
    assert definition is not None
    for raw_name, raw_value in properties.items():
        if raw_name in {DM_JSON_TRAVERSAL_COUNT, DM_JSON_TRAVERSAL_LIMIT}:
            if not source_driven:
                raise DmJsonCodecError(
                    f"{raw_name} is valid only for a source-driven generate element",
                    path=path + (raw_name,),
                )
            name = raw_name
            annotation: object = int
        else:
            name = aliases.get(raw_name, "")
            if not name:
                raise DmJsonCodecError(
                    f"unsupported property {raw_name!r} for element {tag!r}",
                    path=path + (raw_name,),
                )
            if source_driven and name in _source_cardinality_property_names(tag):
                replacement = DM_JSON_TRAVERSAL_COUNT if name == ATTR_COUNT else DM_JSON_TRAVERSAL_LIMIT
                raise DmJsonCodecError(
                    f"source-driven generate uses {replacement!r}, not {raw_name!r}",
                    path=path + (raw_name,),
                )
            annotation = (definition.model.model_fields if definition.model is not None else {})[
                name
            ].rebuild_annotation()
        if name in normalized:
            raise DmJsonCodecError(f"duplicate property spelling for {name!r}", path=path + (raw_name,))
        value = (
            _normalize_source_traversal_count(raw_value, path=path + (name,))
            if name == DM_JSON_TRAVERSAL_COUNT
            else _normalize_property_value(annotation, raw_value, path=path + (name,))
        )
        if name == DM_JSON_TRAVERSAL_LIMIT and (type(value) is not int or value < 1):
            raise DmJsonCodecError("traversal_limit must be a positive integer", path=path + (name,))
        normalized[name] = value
    order = {name: index for index, name in enumerate((*field_order, DM_JSON_TRAVERSAL_COUNT, DM_JSON_TRAVERSAL_LIMIT))}
    return dict(sorted(normalized.items(), key=lambda item: (order.get(item[0], len(order)), item[0])))


def _compile_node(node: DmJsonNodeV1, *, path: tuple[str | int, ...]) -> etree._Element:
    definition = get_element_definition(node.kind)
    if definition is None:  # pragma: no cover - normalized document
        raise DmJsonCodecError(f"unknown DATAMIMIC element {node.kind!r}", path=path + ("kind",))
    attributes = _compile_properties(node.kind, node.properties, path=path + ("properties",))
    if node.content is not None and node.content.kind in {ElementContentModeKind.URI, ElementContentModeKind.SCRIPT}:
        mode = next(item for item in definition.content_modes if item.kind is node.content.kind)
        if len(mode.required_attributes) != 1:
            raise DmJsonCodecError(
                f"content mode {node.content.kind.value!r} does not have one canonical attribute",
                path=path + ("content",),
            )
        attributes[mode.required_attributes[0]] = node.content.value
    element = etree.Element(node.kind)
    for attribute, value in attributes.items():
        try:
            element.set(attribute, value)
        except ValueError as error:
            if node.content is not None and any(
                attribute in mode.required_attributes for mode in definition.content_modes
            ):
                location: tuple[str | int, ...] = ("content", "value")
            else:
                name = project_dm_json_property_name(
                    node.kind, attribute, source_driven=is_source_driven_properties(node.kind, node.properties)
                )
                location = ("properties", name)
            raise DmJsonCodecError("property contains invalid XML characters", path=path + location) from error
    if node.content is not None and node.content.kind in {ElementContentModeKind.TEXT, ElementContentModeKind.INLINE}:
        try:
            element.text = node.content.value
        except ValueError as error:
            raise DmJsonCodecError(
                "content contains invalid XML characters", path=path + ("content", "value")
            ) from error
    for index, child in enumerate(node.children):
        if child.comment is not None:
            element.append(_xml_comment(child.comment, path=path + ("children", index, "comment")))
        element.append(_compile_node(child, path=path + ("children", index)))
    return element


def _compile_properties(
    tag: str,
    properties: Mapping[str, DmJsonScalar],
    *,
    path: tuple[str | int, ...],
) -> dict[str, str]:
    definition = get_element_definition(tag)
    if definition is None:  # pragma: no cover
        raise DmJsonCodecError(f"unknown DATAMIMIC element {tag!r}", path=path)
    fields = definition.model.model_fields if definition.model is not None else {}
    source_driven = is_source_driven_properties(tag, tuple(properties))
    result: dict[str, str] = {}
    for name, raw_value in properties.items():
        if source_driven and name in {DM_JSON_TRAVERSAL_COUNT, DM_JSON_TRAVERSAL_LIMIT}:
            attribute = ATTR_COUNT if name == DM_JSON_TRAVERSAL_COUNT else ATTR_MAX_COUNT
            value: object = raw_value
        else:
            field = fields.get(name)
            if field is None:  # pragma: no cover - normalized document
                raise DmJsonCodecError(f"unsupported property {name!r} for element {tag!r}", path=path + (name,))
            attribute = field.alias if isinstance(field.alias, str) else name
            value = _normalize_property_value(field.rebuild_annotation(), raw_value, path=path + (name,))
        result[attribute] = _xml_scalar(value)
    return result


def _decompile_node(
    element: etree._Element,
    *,
    path: tuple[str | int, ...],
    comment: str | None = None,
) -> DmJsonNodeV1:
    if not isinstance(element.tag, str) or element.tag.startswith("{") or ":" in element.tag:
        raise DmJsonCodecError("namespaced XML elements are not representable in DM JSON", path=path + ("kind",))
    tag = canonical_tag(element.tag)
    definition = get_element_definition(tag)
    if definition is None:
        raise DmJsonCodecError(f"unsupported XML element {element.tag!r}", path=path + ("kind",))
    if element.nsmap:
        raise DmJsonCodecError("XML namespace declarations are not representable", path=path)
    raw_attributes = dict(element.attrib)
    content = _decompile_content(definition.content_modes, raw_attributes, element.text, path=path)
    properties = _decompile_properties(tag, raw_attributes, path=path + ("properties",))
    if any(child.tail and child.tail.strip() for child in element):
        raise DmJsonCodecError("mixed XML child/tail content is not representable", path=path)
    children = _decompile_children(element, path=path)
    return DmJsonNodeV1(kind=element.tag, properties=properties, content=content, comment=comment, children=children)


def _decompile_children(element: etree._Element, *, path: tuple[str | int, ...]) -> tuple[DmJsonNodeV1, ...]:
    """Associate one XML comment with the immediately following descriptor node."""

    children: list[DmJsonNodeV1] = []
    pending_comment: str | None = None
    for raw_child in element:
        if isinstance(raw_child, etree._Comment):
            if pending_comment is not None:
                raise DmJsonCodecError("XML comments must precede exactly one descriptor node", path=path)
            pending_comment = _comment_text(raw_child, path=path + ("children", len(children), "comment"))
            continue
        if not isinstance(raw_child.tag, str):
            raise DmJsonCodecError("unsupported XML node is not representable in DM JSON", path=path)
        children.append(
            _decompile_node(
                raw_child,
                path=path + ("children", len(children)),
                comment=pending_comment,
            )
        )
        pending_comment = None
    if pending_comment is not None:
        raise DmJsonCodecError("XML comment must precede a descriptor node", path=path + ("children",))
    return tuple(children)


def _root_comment(root: etree._Element) -> str | None:
    if root.getnext() is not None:
        raise DmJsonCodecError("XML comment must precede the descriptor root", path=("root", "comment"))
    comments: list[etree._Comment] = []
    sibling = root.getprevious()
    while sibling is not None:
        if not isinstance(sibling, etree._Comment):
            raise DmJsonCodecError("unsupported XML node before descriptor root", path=("xml",))
        comments.append(sibling)
        sibling = sibling.getprevious()
    if len(comments) > 1:
        raise DmJsonCodecError("XML comments must precede exactly one descriptor node", path=("root", "comment"))
    return _comment_text(comments[0], path=("root", "comment")) if comments else None


def _comment_text(comment: etree._Comment, *, path: tuple[str | int, ...]) -> str:
    if not isinstance(comment.text, str):
        raise DmJsonCodecError("invalid XML comment: comment text must not be blank", path=path)
    try:
        normalized = DmJsonNodeV1(kind="comment-holder", comment=comment.text).comment
    except ValidationError as error:
        raise DmJsonCodecError("Invalid XML comment.", path=path) from error
    if normalized is None:  # pragma: no cover - guarded by the explicit input check above
        raise DmJsonCodecError("invalid XML comment: comment text must not be blank", path=path)
    return normalized


def _xml_comment(value: str, *, path: tuple[str | int, ...]) -> etree._Comment:
    try:
        return etree.Comment(value)
    except ValueError as error:
        raise DmJsonCodecError("Invalid XML comment.", path=path) from error


def _decompile_content(
    modes: tuple[ElementContentMode, ...],
    attributes: dict[str, str],
    text: str | None,
    *,
    path: tuple[str | int, ...],
) -> DmJsonContentV1 | None:
    attribute_modes = tuple(
        mode
        for mode in modes
        if mode.kind in {ElementContentModeKind.URI, ElementContentModeKind.SCRIPT}
        and mode.required_attributes
        and all(attribute in attributes for attribute in mode.required_attributes)
    )
    body_modes = tuple(
        mode for mode in modes if mode.kind in {ElementContentModeKind.TEXT, ElementContentModeKind.INLINE}
    )
    body = text if text and (body_modes or text.strip()) else None
    if len(attribute_modes) + (1 if body is not None else 0) > 1:
        raise DmJsonCodecError("multiple XML content modes are not representable", path=path + ("content",))
    if attribute_modes:
        mode = attribute_modes[0]
        if len(mode.required_attributes) != 1:
            raise DmJsonCodecError("multi-attribute content modes are unsupported", path=path + ("content",))
        return DmJsonContentV1(kind=mode.kind, value=attributes.pop(mode.required_attributes[0]))
    if body is not None:
        if len(body_modes) != 1:
            raise DmJsonCodecError("XML body has no unambiguous registered content mode", path=path + ("content",))
        return DmJsonContentV1(kind=body_modes[0].kind, value=body)
    return None


def _decompile_properties(
    tag: str,
    attributes: Mapping[str, str],
    *,
    path: tuple[str | int, ...],
) -> dict[str, DmJsonScalar]:
    definition = get_element_definition(tag)
    if definition is None:  # pragma: no cover
        raise DmJsonCodecError(f"unknown DATAMIMIC element {tag!r}", path=path)
    by_alias: dict[str, tuple[str, object]] = {}
    for name, field in (definition.model.model_fields if definition.model is not None else {}).items():
        by_alias[name] = (name, field.rebuild_annotation())
        if isinstance(field.alias, str):
            by_alias[field.alias] = (name, field.rebuild_annotation())
    source_driven = is_source_driven_properties(tag, tuple(attributes))
    properties: dict[str, DmJsonScalar] = {}
    for attribute, raw_value in attributes.items():
        if source_driven and attribute in {ATTR_COUNT, ATTR_MAX_COUNT}:
            name = project_dm_json_property_name(tag, attribute, source_driven=True)
            annotation: object = int
        else:
            contract = by_alias.get(attribute)
            if contract is None:
                raise DmJsonCodecError(
                    f"XML attribute {attribute!r} on {tag!r} is not representable in DM JSON",
                    path=path + (attribute,),
                )
            name, annotation = contract
        if name in properties:
            raise DmJsonCodecError(f"duplicate property spelling for {name!r}", path=path + (attribute,))
        properties[name] = (
            _normalize_source_traversal_count(raw_value, path=path + (name,))
            if name == DM_JSON_TRAVERSAL_COUNT
            else _normalize_property_value(annotation, raw_value, path=path + (name,))
        )
    return properties


def _normalize_source_traversal_count(
    value: object,
    *,
    path: tuple[str | int, ...],
) -> DmJsonScalar:
    """Keep source traversal cardinality aligned with the runtime ``count`` contract."""

    if type(value) is int:
        if value < 0:
            raise DmJsonCodecError("traversal_count must be a non-negative integer", path=path)
        return value
    if not isinstance(value, str):
        raise DmJsonCodecError("traversal_count must be a non-negative integer or runtime expression", path=path)
    try:
        normalized = check_is_digit_or_script(value)
    except ValueError as error:
        raise DmJsonCodecError("Property must be a non-negative count or runtime expression.", path=path) from error
    return int(normalized) if normalized.isdigit() else normalized


def _normalize_property_value(
    annotation: object,
    value: object,
    *,
    path: tuple[str | int, ...],
) -> DmJsonScalar:
    assert annotation is not None
    adapter: TypeAdapter[object] = TypeAdapter(annotation)
    try:
        normalized = adapter.dump_python(adapter.validate_python(value), mode="json")
    except ValidationError as direct_error:
        if type(value) not in {int, float, bool}:
            raise _property_validation_error(direct_error, path) from direct_error
        try:
            normalized = adapter.dump_python(adapter.validate_python(str(value)), mode="json")
        except ValidationError as string_error:
            raise _property_validation_error(direct_error, path) from string_error
    if isinstance(normalized, bool | str | int | float):
        return normalized
    raise DmJsonCodecError("XML-backed properties must normalize to JSON scalars", path=path)


def _property_validation_error(error: ValidationError, path: tuple[str | int, ...]) -> DmJsonCodecError:
    validation_types: list[JsonValue] = [
        kind
        for kind in sorted(
            {detail["type"] for detail in error.errors(include_input=False, include_context=False, include_url=False)}
        )
    ]
    return DmJsonCodecError(
        "Property failed registered DSL validation.",
        path=path,
        expected={"validation_error_types": validation_types},
    )


def _xml_scalar(value: object) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) in {str, int, float}:
        return str(value)
    raise TypeError(f"unsupported XML scalar {type(value).__name__}")


def _enum_member_name(tag: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", tag).strip("_").upper() or "ELEMENT"


def _project_dm_json_variants_into_schema(schema: Mapping[str, object]) -> dict[str, object]:
    projected = deepcopy(dict(schema))
    raw_definitions = projected.get("$defs")
    if not isinstance(raw_definitions, dict) or "DmJsonNodeV1" not in raw_definitions:
        return projected
    tags = tuple(dict.fromkeys(canonical_tag(tag) for tag in list_element_tags()))
    mapping: dict[str, str] = {}
    for tag in tags:
        definition_name = f"DmJsonNode_{_enum_member_name(tag)}"
        mapping[tag] = f"#/$defs/{definition_name}"
        raw_definitions[definition_name] = _node_variant_schema(tag)
    raw_definitions["DmJsonNodeV1"] = {
        "discriminator": {"propertyName": "kind", "mapping": mapping},
        "oneOf": [{"$ref": reference} for reference in mapping.values()],
        "title": "DmJsonNodeV1",
    }

    def restrict_root(value: object) -> None:
        if isinstance(value, dict):
            if value.get("title") == "DmJsonDocumentV1":
                properties = value.get("properties")
                if isinstance(properties, dict):
                    properties["root"] = {"$ref": "#/$defs/DmJsonNode_SETUP"}
            for child in value.values():
                restrict_root(child)
        elif isinstance(value, list):
            for child in value:
                restrict_root(child)

    restrict_root(projected)
    return projected


def _node_variant_schema(tag: str) -> dict[str, object]:
    definition = get_element_definition(tag)
    if definition is None:  # pragma: no cover - closed registry iteration
        raise ValueError(f"unknown DATAMIMIC element kind {tag!r}")
    content_variants = [
        {
            "type": "object",
            "properties": {"kind": {"const": mode.kind.value}, "value": {"type": "string", "minLength": 1}},
            "required": ["kind", "value"],
            "additionalProperties": False,
        }
        for mode in definition.content_modes
    ]
    content_schema: dict[str, object] = (
        {"anyOf": [*content_variants, {"type": "null"}], "default": None}
        if content_variants
        else {"type": "null", "default": None}
    )
    children_schema: dict[str, object] = {
        "type": "array",
        "items": {"$ref": "#/$defs/DmJsonNodeV1"},
        "default": [],
    }
    node_schema: dict[str, object] = {
        "type": "object",
        "title": f"DM JSON {tag}",
        "properties": {
            "kind": {"const": tag, "type": "string"},
            "properties": _properties_schema(tag),
            "content": content_schema,
            "comment": {
                "type": "string",
                "minLength": 1,
                "description": "Business-friendly XML comment shown immediately before this descriptor node.",
            },
            "children": children_schema,
        },
        "required": ["kind"],
        "additionalProperties": False,
    }
    node_schema["x-datamimic-constraints"] = serialize_constraints(element_constraints(tag))
    node_schema["x-datamimic-bounded-strategy"] = definition.bounded_execution_profile.strategy.value
    node_schema["x-datamimic-singleton-children"] = sorted(definition.singleton_children)
    if definition.allowed_children is not None:
        node_schema["x-datamimic-valid-children"] = sorted(definition.allowed_children)
        if not definition.allowed_children:
            children_schema["maxItems"] = 0
        else:
            children_schema["items"] = {
                "oneOf": [
                    {"$ref": f"#/$defs/DmJsonNode_{_enum_member_name(child)}"}
                    for child in sorted({canonical_tag(child) for child in definition.allowed_children})
                ]
            }
    return node_schema


def _properties_schema(tag: str) -> dict[str, object]:
    definition = get_element_definition(tag)
    if definition is None:
        return {"type": "object", "properties": {}, "additionalProperties": False, "default": {}}
    properties: dict[str, object] = {}
    required: list[str] = []
    content_attributes = {name for mode in definition.content_modes for name in mode.required_attributes}
    for name, field in (definition.model.model_fields if definition.model is not None else {}).items():
        if name in content_attributes or field.alias in content_attributes:
            continue
        field_schema = _inline_type_schema(field.rebuild_annotation())
        if field.description:
            field_schema.setdefault("description", field.description)
        if field.examples and "examples" not in field_schema:
            field_schema["examples"] = field.examples
        properties[name] = field_schema
        if field.is_required():
            required.append(name)
    if tag != EL_GENERATE:
        result: dict[str, object] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
            "default": {},
        }
        if required:
            result["required"] = required
        return result
    source_cardinality_names = _source_cardinality_property_names(tag)
    source_properties = {name: value for name, value in properties.items() if name not in source_cardinality_names}
    source_properties[DM_JSON_TRAVERSAL_COUNT] = {
        "anyOf": [
            {"type": "integer", "minimum": 0},
            {"type": "string", "pattern": r"^\{.+\}$"},
        ],
        "description": "Exact number of source candidates requested for traversal.",
    }
    source_properties[DM_JSON_TRAVERSAL_LIMIT] = {
        "type": "integer",
        "minimum": 1,
        "description": "Maximum number of source candidates traversed.",
    }
    source_required = sorted(set(required).difference(source_cardinality_names) | {ATTR_SOURCE})
    generated_properties = {name: value for name, value in properties.items() if name != ATTR_SOURCE}
    generated_required = [name for name in required if name != ATTR_SOURCE]
    return {
        "oneOf": [
            {
                "title": "Source-driven generate properties",
                "type": "object",
                "properties": source_properties,
                "required": source_required,
                "additionalProperties": False,
            },
            {
                "title": "Generated or operation-driven generate properties",
                "type": "object",
                "properties": generated_properties,
                "required": generated_required,
                "additionalProperties": False,
            },
        ],
        "default": {},
    }


def _inline_type_schema(annotation: object) -> dict[str, object]:
    assert annotation is not None
    raw_schema = TypeAdapter(annotation).json_schema()
    definitions = raw_schema.pop("$defs", {})

    def inline(value: object, stack: frozenset[str] = frozenset()) -> object:
        if isinstance(value, list):
            return [inline(item, stack) for item in value]
        if not isinstance(value, dict):
            return value
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            name = reference.rsplit("/", maxsplit=1)[-1]
            target = definitions.get(name)
            if isinstance(target, dict) and name not in stack:
                siblings = {key: item for key, item in value.items() if key != "$ref"}
                resolved = inline(target, stack | {name})
                if isinstance(resolved, dict):
                    inlined_siblings = inline(siblings, stack)
                    assert isinstance(inlined_siblings, dict)
                    return {**resolved, **inlined_siblings}
        return {key: inline(item, stack) for key, item in value.items()}

    inlined = inline(raw_schema)
    if not isinstance(inlined, dict):  # pragma: no cover - Pydantic contract
        raise TypeError("Pydantic field schema must be a JSON object")
    variants = inlined.get("anyOf")
    if isinstance(variants, list):
        scalar_variants = [
            variant for variant in variants if not isinstance(variant, dict) or variant.get("type") != "null"
        ]
        if len(scalar_variants) == 1:
            inlined = {**scalar_variants[0], **{key: value for key, value in inlined.items() if key != "anyOf"}}
        elif scalar_variants:
            inlined["anyOf"] = scalar_variants
    return {str(key): value for key, value in inlined.items()}
