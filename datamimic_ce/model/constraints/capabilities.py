# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Source-file-format and capability facts for ``source=``-aware elements."""

from dataclasses import dataclass

from datamimic_ce._compat import StrEnum

# Attribute constants (imported at module level to avoid circular imports)
from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_DICT,
    DATA_TYPE_LIST,
)
from datamimic_ce.constants.element_constants import (
    EL_ELEMENT,
    EL_GENERATE,
    EL_ID,
    EL_ITERATE,
    EL_KEY,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_VARIABLE,
)


class DynamicSourceKind(StrEnum):
    PYTHON_EXPRESSION = "python_expression"
    BRACED_EXPRESSION = "braced_expression"


class SourceFileFormat(StrEnum):
    """Canonical runtime file formats accepted by ``source=`` consumers."""

    DBUNIT_XML = ".dbunit.xml"
    WEIGHTED_ENTITY_CSV = ".wgt.ent.csv"
    WEIGHTED_CSV = ".wgt.csv"
    CSV = ".csv"
    JSON = ".json"
    XLSX = ".xlsx"
    XML = ".xml"
    FIXED_WIDTH = ".fcw"


@dataclass(frozen=True)
class SourceCapability:
    """One runtime-supported ``source=`` context.

    ``source_type`` narrows shape-sensitive consumers such as ``nestedKey``.
    ``DataSourceRegistry`` owns runtime loading and routing; this fact owns which
    source kinds and suffixes that boundary allows each element to dispatch.
    """

    element: str
    file_formats: tuple[SourceFileFormat, ...] = ()
    source_type: str | None = None
    allows_memstore: bool = False
    allows_client: bool = False
    dynamic_source: DynamicSourceKind | None = None


_SOURCE_CAPABILITIES: tuple[SourceCapability, ...] = (
    SourceCapability(
        EL_GENERATE,
        (
            SourceFileFormat.DBUNIT_XML,
            SourceFileFormat.CSV,
            SourceFileFormat.JSON,
            SourceFileFormat.XLSX,
            SourceFileFormat.XML,
            SourceFileFormat.FIXED_WIDTH,
        ),
        allows_memstore=True,
        allows_client=True,
    ),
    SourceCapability(
        EL_ITERATE,
        (
            SourceFileFormat.DBUNIT_XML,
            SourceFileFormat.CSV,
            SourceFileFormat.JSON,
            SourceFileFormat.XLSX,
            SourceFileFormat.XML,
            SourceFileFormat.FIXED_WIDTH,
        ),
        allows_memstore=True,
        allows_client=True,
    ),
    SourceCapability(
        EL_VARIABLE,
        (
            SourceFileFormat.WEIGHTED_ENTITY_CSV,
            SourceFileFormat.CSV,
            SourceFileFormat.JSON,
            SourceFileFormat.XLSX,
            SourceFileFormat.FIXED_WIDTH,
        ),
        allows_memstore=True,
        allows_client=True,
        dynamic_source=DynamicSourceKind.PYTHON_EXPRESSION,
    ),
    SourceCapability(
        EL_NESTED_KEY,
        allows_memstore=True,
        dynamic_source=DynamicSourceKind.BRACED_EXPRESSION,
    ),
    SourceCapability(
        EL_NESTED_KEY,
        (SourceFileFormat.CSV, SourceFileFormat.JSON),
        source_type=DATA_TYPE_LIST,
    ),
    SourceCapability(EL_NESTED_KEY, (SourceFileFormat.JSON,), source_type=DATA_TYPE_DICT),
    SourceCapability(EL_KEY, (SourceFileFormat.WEIGHTED_CSV,)),
    SourceCapability(EL_ID, (SourceFileFormat.WEIGHTED_CSV,)),
    SourceCapability(EL_ELEMENT, (SourceFileFormat.WEIGHTED_CSV,)),
    SourceCapability(EL_REFERENCE, allows_client=True),
)


def source_capabilities() -> tuple[SourceCapability, ...]:
    """Return the immutable runtime source-capability catalog."""

    return _SOURCE_CAPABILITIES


def serialize_source_capability(capability: SourceCapability) -> dict[str, object]:
    """Project one source-capability fact to reference/capabilities JSON."""

    return {
        "element": capability.element,
        "source_type": capability.source_type,
        "file_suffixes": [file_format.value for file_format in capability.file_formats],
        "allows_memstore": capability.allows_memstore,
        "allows_client": capability.allows_client,
        "dynamic_source": capability.dynamic_source.value if capability.dynamic_source is not None else None,
    }


def _source_capabilities_for(element: str, source_type: str | None = None) -> tuple[SourceCapability, ...]:
    return tuple(
        capability
        for capability in _SOURCE_CAPABILITIES
        if capability.element == element and capability.source_type in (None, source_type)
    )


def supported_source_file_formats(
    element: str,
    source_type: str | None = None,
) -> tuple[SourceFileFormat, ...]:
    """File formats accepted by one element/shape, longest suffix first."""

    formats = {
        file_format
        for capability in _source_capabilities_for(element, source_type)
        for file_format in capability.file_formats
    }
    return tuple(sorted(formats, key=lambda file_format: (-len(file_format.value), file_format.value)))


def recognized_source_file_formats() -> tuple[SourceFileFormat, ...]:
    """All file formats known anywhere in CE, for unsupported-context diagnostics."""

    formats = {file_format for capability in _SOURCE_CAPABILITIES for file_format in capability.file_formats}
    return tuple(sorted(formats, key=lambda file_format: (-len(file_format.value), file_format.value)))


def source_file_format(source: str) -> SourceFileFormat | None:
    """Return a file format recognized by any runtime source context, if present."""

    return next(
        (file_format for file_format in recognized_source_file_formats() if source.endswith(file_format.value)),
        None,
    )


def source_file_format_for(
    element: str,
    source: str,
    source_type: str | None = None,
) -> SourceFileFormat | None:
    """Return the typed format this concrete runtime source context dispatches."""

    return next(
        (
            file_format
            for file_format in supported_source_file_formats(element, source_type)
            if source.endswith(file_format.value)
        ),
        None,
    )


def is_source_file(source: str, element: str, source_type: str | None = None) -> bool:
    """Whether one concrete runtime source context supports ``source`` as a file."""

    return source_file_format_for(element, source, source_type) is not None


def source_allows_memstore(element: str, source_type: str | None = None) -> bool:
    return any(capability.allows_memstore for capability in _source_capabilities_for(element, source_type))


def source_allows_client(element: str, source_type: str | None = None) -> bool:
    return any(capability.allows_client for capability in _source_capabilities_for(element, source_type))


def source_dynamic_kind(element: str, source_type: str | None = None) -> DynamicSourceKind | None:
    return next(
        (
            capability.dynamic_source
            for capability in _source_capabilities_for(element, source_type)
            if capability.dynamic_source is not None
        ),
        None,
    )
