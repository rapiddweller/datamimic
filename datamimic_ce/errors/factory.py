# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

import os
from typing import overload

from datamimic_ce.errors.base import (
    ClientConfigError,
    ConditionEvaluationError,
    DateTimeConversionError,
    DomainError,
    EntityInitError,
    ExportConfigError,
    GeneratorConfigError,
    IncludeError,
    InvalidDatasetError,
    InvalidLocaleError,
    InvalidSourceError,
    MissingDescriptorError,
    MissingIncludeError,
    MissingMemstoreProductError,
    OperationError,
    ParserValidationError,
    RuleEvaluationError,
    RuntimeConfigError,
    TaskConfigError,
    UserErrorBase,
    UserRuntimeError,
    UserValueError,
)
from datamimic_ce.errors.catalog import IssueCode
from datamimic_ce.errors.codes import ErrorCode
from datamimic_ce.errors.context import DescriptorLocation
from datamimic_ce.errors.descriptor_contracts import DescriptorCarrierLike
from datamimic_ce.errors.formatters import (
    client_config_message,
    condition_evaluation_message,
    dataset_message,
    datetime_conversion_message,
    descriptor_hint,
    descriptor_hint_if_missing,
    entity_init_error_message,
    export_config_message,
    generator_config_message,
    include_message,
    invalid_locale_message,
    invalid_source_message,
    operation_message,
    parser_validation_message,
    rule_error_message,
    runtime_config_message,
    task_config_message,
    warning_message,
)

# task_warning is fire-and-forget + idempotent per rendered message → dedup here (parity with the
# model-layer flood guard) so the same combination warns once, not once per re-parse/worker.
_emitted_warnings: set[tuple[int, str]] = set()


def task_warning(*, code: IssueCode, once: bool = True, **kwargs: object) -> None:
    """Emit a catalog warning once per process and rendered message; once=False always emits.

    The warning analog of ``task_config_error`` — same catalog, same drift-gated templating, same
    maintenance — differing only in that a warning is logged, not raised (severity is data on the
    IssueDefinition; a non-WARNING code here is a wiring bug)."""
    import logging

    from datamimic_ce.errors.catalog import get_issue_definition
    from datamimic_ce.errors.codes import IssueSeverity
    from datamimic_ce.errors.formatters import DEFAULT_LOGGER_NAME

    logger = logging.getLogger(DEFAULT_LOGGER_NAME)

    if get_issue_definition(code).severity is not IssueSeverity.WARNING:
        raise ValueError(f"{code} is not a WARNING-severity issue; raise it with the error factory instead.")
    msg = warning_message(code=code, **kwargs)
    key = (os.getpid(), msg)
    if not once or key not in _emitted_warnings:
        if once:
            _emitted_warnings.add(key)
        logger.warning("%s", msg)


def _append_descriptor_hint(message: str, ctx: DescriptorCarrierLike | None, descriptor_name: str | None) -> str:
    hint = descriptor_hint_if_missing(message, ctx, descriptor_name)
    if not hint:
        return message
    normalized = message.rstrip()
    if normalized.endswith((".", "!", "?", ":", ";")):
        normalized = normalized[:-1].rstrip()
    return f"{normalized}{hint}"


def tag_user_error(err: Exception) -> Exception:
    """Wrap an exception as a user-facing config error (for log UX)."""
    if isinstance(err, (UserErrorBase, DomainError)):
        # WHY: preserve typed user errors rather than re-wrapping and losing context.
        return err
    # WHY: avoid dynamic class creation without a proven multiprocessing requirement.
    cls = UserValueError if isinstance(err, ValueError) else UserRuntimeError
    wrapped = cls(str(err))
    wrapped.__cause__ = err
    return wrapped


@overload
def user_error(
    message: str,
    *,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    exc_type: type[ValueError],
) -> ValueError: ...


@overload
def user_error(
    message: str,
    *,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    exc_type: type[RuntimeError] = RuntimeError,
) -> RuntimeError: ...


def user_error(
    message: str,
    *,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    exc_type: type[ValueError] | type[RuntimeError] = RuntimeError,
) -> ValueError | RuntimeError:
    """Create a user-facing error with descriptor context attached."""
    if exc_type in (RuntimeError, ValueError):
        # Allowed base exception types; we always wrap into the stable user-facing variants below.
        pass
    elif issubclass(exc_type, UserErrorBase):
        # WHY: typed user errors must be created via factories (SPOT) to keep codes/templates consistent.
        raise ValueError("Use factory helpers for typed user errors (invalid exc_type).")
    else:
        # WHY: keep the user-facing wrapper taxonomy small and stable (pickling + log UX).
        raise ValueError("user_error supports only ValueError/RuntimeError.")
    # WHY: stable mapping to static user error wrappers keeps behavior deterministic.
    cls = UserValueError if issubclass(exc_type, ValueError) else UserRuntimeError
    return cls(f"{message}{descriptor_hint(ctx, descriptor_name)}")


def invalid_dataset_error(
    *,
    dataset: str | None,
    entity: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
) -> InvalidDatasetError:
    msg = dataset_message(dataset=dataset, entity=entity)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return InvalidDatasetError(msg, dataset=dataset)


def datetime_conversion_error(
    *,
    element_tag: str,
    name: str,
    in_fmt: str | None,
    out_fmt: str | None,
    cause: str,
    input_empty: bool = False,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
) -> DateTimeConversionError:
    msg = datetime_conversion_message(
        element_tag=element_tag,
        name=name,
        in_fmt=in_fmt,
        out_fmt=out_fmt,
        cause=cause,
        input_empty=input_empty,
    )
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return DateTimeConversionError(msg, location=location)


def entity_init_error(
    *,
    var_name: str,
    entity: str,
    cause: str,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
) -> EntityInitError:
    msg = entity_init_error_message(var_name=var_name, entity=entity, cause=cause)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return EntityInitError(msg)


def invalid_source_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> InvalidSourceError:
    msg = invalid_source_message(code=code, guidance=guidance, **kwargs)
    msg = _append_descriptor_hint(msg, ctx, descriptor_name)
    return InvalidSourceError(msg, issue_code=code, location=location)


def export_config_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> ExportConfigError:
    msg = export_config_message(code=code, guidance=guidance, **kwargs)
    msg = _append_descriptor_hint(msg, ctx, descriptor_name)
    return ExportConfigError(msg, issue_code=code, location=location)


def include_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> IncludeError:
    msg = include_message(code=code, guidance=guidance, **kwargs)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    error_type = MissingIncludeError if code is IssueCode.INCLUDE_FILE_NOT_FOUND else IncludeError
    return error_type(msg, issue_code=code, location=location)


def generator_config_error(
    *,
    code: IssueCode | None = None,
    reason: str | None = None,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> GeneratorConfigError:
    inline_descriptor = code == IssueCode.GENERATOR_CREATE_FAILED
    if inline_descriptor:
        kwargs["descriptor"] = descriptor_hint(ctx, descriptor_name) or kwargs.get("descriptor", "")
    msg = generator_config_message(code=code, reason=reason, guidance=guidance, **kwargs)
    if not inline_descriptor:
        msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    error = GeneratorConfigError(msg, issue_code=code, location=location)
    error.constructor_reason = reason
    return error


def condition_evaluation_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> ConditionEvaluationError:
    msg = condition_evaluation_message(code=code, guidance=guidance, **kwargs)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return ConditionEvaluationError(msg, issue_code=code, location=location)


def parser_validation_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    validation_errors: tuple[dict[str, object], ...] = (),
    **kwargs: object,
) -> ParserValidationError:
    msg = parser_validation_message(code=code, guidance=guidance, location=location, **kwargs)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    error_type = MissingDescriptorError if code is IssueCode.PARSER_DESCRIPTOR_NOT_FOUND else ParserValidationError
    error = error_type(msg, issue_code=code, location=location)
    error.validation_errors = validation_errors
    return error


def client_config_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> ClientConfigError:
    msg = client_config_message(code=code, guidance=guidance, **kwargs)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return ClientConfigError(msg, issue_code=code, location=location)


def runtime_config_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> RuntimeConfigError:
    msg = runtime_config_message(code=code, guidance=guidance, **kwargs)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return RuntimeConfigError(msg, issue_code=code, location=location)


def task_config_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> TaskConfigError:
    script_error = code == IssueCode.TASK_SCRIPT_ERROR
    if script_error:
        kwargs["descriptor"] = descriptor_hint(ctx, descriptor_name) or kwargs.get("descriptor", "")
    msg = task_config_message(code=code, guidance=guidance, **kwargs)
    if not script_error:
        msg = _append_descriptor_hint(msg, ctx, descriptor_name)
    return TaskConfigError(msg, issue_code=code, location=location)


def operation_error(
    *,
    code: IssueCode,
    guidance: str | None = None,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    location: DescriptorLocation | None = None,
    **kwargs: object,
) -> OperationError:
    msg = operation_message(code=code, guidance=guidance, **kwargs)
    msg = f"{msg}{descriptor_hint(ctx, descriptor_name)}"
    return OperationError(msg, issue_code=code, location=location)


def rule_evaluation_error(
    *,
    expr: str,
    element_tag: str,
    ctx: DescriptorCarrierLike | None = None,
    descriptor_name: str | None = None,
    kind: str = "condition",
    cause: str | None = None,
) -> RuleEvaluationError:
    msg = rule_error_message(
        expr,
        element_tag=element_tag,
        ctx=ctx,
        descriptor_name=descriptor_name,
        kind=kind,
        cause=cause,
    )
    return RuleEvaluationError(msg)


def ensure_user_error(err: Exception) -> Exception:
    """Return the error if already user-facing, otherwise wrap it."""
    if isinstance(err, (UserErrorBase, DomainError)):
        return err
    return tag_user_error(err)


def invalid_locale_error(locale: str, *, hint: str, path: str, request_hash: str) -> InvalidLocaleError:
    return InvalidLocaleError(
        code=ErrorCode.INVALID_LOCALE,
        message=invalid_locale_message(locale),
        hint=hint,
        path=path,
        request_hash=request_hash,
        locale=locale,
    )


def missing_memstore_product_error(product_type: str | None) -> MissingMemstoreProductError:
    return MissingMemstoreProductError(f"Data naming '{product_type}' is empty in memstore", product_type=product_type)
