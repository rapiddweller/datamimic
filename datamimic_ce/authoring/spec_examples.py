# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Minimal canonical intent examples shared by validation and reference projection."""

from collections.abc import Callable, Mapping

from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    ExactCountExpectation,
    FileExportTarget,
    FileSource,
    ForeignKeyRole,
    GeneratedProduct,
    IdentifierRole,
    IncrementField,
    MemstoreSource,
    MemstoreTarget,
    NestedGeneratedProduct,
    PerParentCountExpectation,
    PersonNameField,
    ProductIntent,
    ProductIntentKind,
    ScriptField,
    SourceIntentKind,
    SourceProduct,
    TimeSeriesProduct,
    TimeSeriesWindow,
    TimestampRole,
)


def _generated_product() -> GeneratedProduct:
    return GeneratedProduct(
        name="records",
        count=5,
        fields=(IncrementField(name="id", roles=(IdentifierRole(),)),),
    )


def _source_product() -> SourceProduct:
    return SourceProduct(
        name="records",
        source=FileSource(path="input.csv", separator=","),
        fields=(ScriptField(name="id", script="id"),),
    )


def _time_series_product() -> TimeSeriesProduct:
    return TimeSeriesProduct(
        name="measurements",
        series_count=1,
        window=TimeSeriesWindow(
            start="2026-01-01T00:00:00Z",
            end="2026-01-01T01:00:00Z",
            interval="PT15M",
        ),
        fields=(ScriptField(name="observed_at", script="ts.now", roles=(TimestampRole(),)),),
    )


def _file_source() -> FileSource:
    return FileSource(path="input.csv", separator=",")


def _memstore_source() -> MemstoreSource:
    return MemstoreSource(id="records_store", product="records")


_PRODUCT_FACTORIES: Mapping[ProductIntentKind, Callable[[], ProductIntent]] = {
    ProductIntentKind.GENERATED: _generated_product,
    ProductIntentKind.SOURCE: _source_product,
    ProductIntentKind.TIME_SERIES: _time_series_product,
}
_SOURCE_FACTORIES: Mapping[
    SourceIntentKind,
    Callable[[], FileSource | MemstoreSource],
] = {
    SourceIntentKind.FILE: _file_source,
    SourceIntentKind.MEMSTORE: _memstore_source,
}


def minimal_product_example(kind: ProductIntentKind) -> ProductIntent:
    """Construct a minimal product through its exact canonical Pydantic subtype."""

    return _PRODUCT_FACTORIES[kind]()


def minimal_source_product_example() -> SourceProduct:
    """Construct the canonical minimal source product."""

    return _source_product()


def minimal_time_series_product_example() -> TimeSeriesProduct:
    """Construct the canonical minimal time-series product."""

    return _time_series_product()


def minimal_source_example(kind: SourceIntentKind) -> FileSource | MemstoreSource:
    """Construct an exact source-union variant from the Intent Model SPOT."""

    return _SOURCE_FACTORIES[kind]()


def flat_authoring_example() -> AuthoringSpecV1:
    """Construct the canonical flat authoring example."""

    return AuthoringSpecV1(
        seed=42,
        products=(
            GeneratedProduct(
                name="customers",
                count=5,
                fields=(
                    IncrementField(name="customer_id", roles=(IdentifierRole(),)),
                    PersonNameField(name="name"),
                ),
                targets=(FileExportTarget(format="JSON"),),
            ),
        ),
        expectations=(ExactCountExpectation(product="customers", count=5),),
    )


def nested_authoring_example() -> AuthoringSpecV1:
    """Construct the single canonical direct parent-child example."""

    return AuthoringSpecV1(
        seed=42,
        products=(
            GeneratedProduct(
                name="customers",
                count=4,
                fields=(
                    IncrementField(name="customer_id", roles=(IdentifierRole(),)),
                ),
                children=(
                    NestedGeneratedProduct(
                        name="orders",
                        count=2,
                        fields=(
                            IncrementField(name="order_no"),
                            ScriptField(
                                name="customer_id",
                                script="parent.customer_id",
                                roles=(
                                    ForeignKeyRole(
                                        parent_product="customers",
                                        parent_field="customer_id",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        expectations=(
            PerParentCountExpectation(
                parent_product="customers",
                child_product="orders",
                count=2,
            ),
        ),
    )


def source_authoring_example() -> AuthoringSpecV1:
    """Construct the canonical file-source example."""

    return AuthoringSpecV1(seed=42, products=(minimal_source_product_example(),))


def time_series_authoring_example() -> AuthoringSpecV1:
    """Construct the canonical time-series example."""

    return AuthoringSpecV1(seed=42, products=(minimal_time_series_product_example(),))


def memstore_pipeline_authoring_example() -> AuthoringSpecV1:
    """Construct an acceptance-ready producer and memstore read-back pipeline."""

    return AuthoringSpecV1(
        seed=42,
        products=(
            GeneratedProduct(
                name="records",
                count=5,
                fields=(IncrementField(name="record_id", roles=(IdentifierRole(),)),),
                targets=(MemstoreTarget(id="records_store"),),
            ),
            SourceProduct(
                name="record_readback",
                source=MemstoreSource(id="records_store", product="records"),
                fields=(
                    ScriptField(
                        name="record_id",
                        script="record_id",
                        roles=(
                            ForeignKeyRole(
                                parent_product="records",
                                parent_field="record_id",
                            ),
                        ),
                    ),
                ),
            ),
        ),
        expectations=(
            ExactCountExpectation(product="record_readback", count=5),
        ),
    )


def product_example_kinds() -> frozenset[ProductIntentKind]:
    """Expose registry coverage for SPOT drift gates."""

    return frozenset(_PRODUCT_FACTORIES)


def source_example_kinds() -> frozenset[SourceIntentKind]:
    """Expose source factory coverage for SPOT drift gates."""

    return frozenset(_SOURCE_FACTORIES)


__all__ = [
    "flat_authoring_example",
    "memstore_pipeline_authoring_example",
    "minimal_product_example",
    "minimal_source_example",
    "minimal_source_product_example",
    "minimal_time_series_product_example",
    "nested_authoring_example",
    "product_example_kinds",
    "source_authoring_example",
    "source_example_kinds",
    "time_series_authoring_example",
]
