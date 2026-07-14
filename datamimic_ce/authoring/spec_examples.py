# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Minimal canonical intent examples shared by validation and reference projection."""

from collections.abc import Callable, Mapping

from datamimic_ce.authoring.spec import (
    FileSource,
    GeneratedProduct,
    IdentifierRole,
    IncrementField,
    ProductIntent,
    ProductIntentKind,
    ScriptField,
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


_PRODUCT_FACTORIES: Mapping[ProductIntentKind, Callable[[], ProductIntent]] = {
    ProductIntentKind.GENERATED: _generated_product,
    ProductIntentKind.SOURCE: _source_product,
    ProductIntentKind.TIME_SERIES: _time_series_product,
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


def product_example_kinds() -> frozenset[ProductIntentKind]:
    """Expose registry coverage for SPOT drift gates."""

    return frozenset(_PRODUCT_FACTORIES)


__all__ = [
    "minimal_product_example",
    "minimal_source_product_example",
    "minimal_time_series_product_example",
    "product_example_kinds",
]
