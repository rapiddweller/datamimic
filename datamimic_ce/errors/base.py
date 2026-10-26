from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

from datamimic_ce.errors.codes import DomainErrorCode, ErrorCode, IssueCode
from datamimic_ce.errors.context import DescriptorLocation


@dataclass(frozen=True)
class DomainError(Exception):
    code: DomainErrorCode | ErrorCode
    message: str
    hint: str | None
    path: str
    request_hash: str
    details: dict[str, object] | None = None

    def __reduce__(self) -> tuple[object, tuple[object, ...]]:
        return _restore_domain_error, (
            self.code,
            self.message,
            self.hint,
            self.path,
            self.request_hash,
            self.details,
            self.__cause__,
        )

    def __str__(self) -> str:
        return ""

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code.value,
            "message": self.message,
            "path": self.path,
            "request_hash": self.request_hash,
        }
        if self.hint:
            payload["hint"] = self.hint
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class InvalidLocaleError(ValueError, DomainError):
    """CE 5.0 aligns the Python locale error code and message with EE's E002 contract."""

    locale: str | None = None

    def __str__(self) -> str:
        return self.message

    def __reduce__(self) -> tuple[object, tuple[object, ...]]:
        return _restore_locale_error, (
            self.code,
            self.message,
            self.hint,
            self.path,
            self.request_hash,
            self.details,
            self.locale,
            self.__cause__,
        )


def _restore_domain_error(
    code: DomainErrorCode | ErrorCode,
    message: str,
    hint: str | None,
    path: str,
    request_hash: str,
    details: dict[str, object] | None,
    cause: BaseException | None,
) -> DomainError:
    error = DomainError(code, message, hint, path, request_hash, details)
    object.__setattr__(error, "__cause__", cause)
    return error


def _restore_locale_error(
    code: DomainErrorCode | ErrorCode,
    message: str,
    hint: str | None,
    path: str,
    request_hash: str,
    details: dict[str, object] | None,
    locale: str | None,
    cause: BaseException | None,
) -> InvalidLocaleError:
    error = InvalidLocaleError(code, message, hint, path, request_hash, details, locale)
    object.__setattr__(error, "__cause__", cause)
    return error


class _UserErrorState(TypedDict):
    code: ErrorCode | None
    issue_code: IssueCode | None
    location: DescriptorLocation | None
    dataset: NotRequired[str | None]
    product_type: NotRequired[str | None]
    validation_errors: NotRequired[tuple[dict[str, object], ...]]
    constructor_reason: NotRequired[str | None]


class UserErrorBase(Exception):
    """Marker base for user-facing errors (no attribute flags)."""

    error_code: ErrorCode | None = None

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode | None = None,
        issue_code: IssueCode | None = None,
        location: DescriptorLocation | None = None,
    ) -> None:
        super().__init__(message)
        self.code: ErrorCode | None = code or self.error_code
        self.issue_code = issue_code
        self.location = location

    def __reduce__(self) -> tuple[object, tuple[object, ...]]:
        state = _UserErrorState(code=self.code, issue_code=self.issue_code, location=self.location)
        if isinstance(self, InvalidDatasetError):
            state["dataset"] = self.dataset
        if isinstance(self, MissingMemstoreProductError):
            state["product_type"] = self.product_type
        if isinstance(self, ParserValidationError):
            state["validation_errors"] = self.validation_errors
        if isinstance(self, GeneratorConfigError):
            state["constructor_reason"] = self.constructor_reason
        return _restore_user_error, (type(self), str(self.args[0]), state, self.__cause__)


class UserRuntimeError(UserErrorBase, RuntimeError):
    """User-facing RuntimeError (stable class for multiprocessing pickling)."""


class UserValueError(UserErrorBase, ValueError):
    """User-facing ValueError (stable class for multiprocessing pickling)."""


class InvalidDatasetError(UserValueError):
    """Typed user error for unsupported datasets."""

    error_code = ErrorCode.INVALID_DATASET

    def __init__(self, message: str, *, dataset: str | None = None):
        super().__init__(message)
        self.dataset = dataset


class DateTimeConversionError(UserValueError):
    """Typed user error for datetime conversion failures."""

    error_code = ErrorCode.DATETIME_CONVERSION_FAILED


class EntityInitError(UserValueError):
    """Typed user error for entity initialization failures."""

    error_code = ErrorCode.ENTITY_INIT_FAILED


class InvalidSourceError(UserValueError):
    """Typed user error for invalid source configuration."""

    error_code = ErrorCode.INVALID_SOURCE


class MissingSourceError(InvalidSourceError, FileNotFoundError):
    """Keep missing-resource catch compatibility alongside the source identity."""


class MissingMemstoreProductError(InvalidSourceError, KeyError):
    """A declared in-memory source has not received the requested product."""

    guidance = (
        "Generate the requested product into the memstore before reading it. A product writes the entity named by "
        "targetEntity, else its name; a source reads sourceEntity, else type, else its name."
    )

    def __init__(self, message: str, *, product_type: str | None = None) -> None:
        super().__init__(message)
        self.product_type = product_type


class RuleEvaluationError(UserRuntimeError):
    """Typed user error for rule/condition evaluation failures."""

    error_code = ErrorCode.RULE_EVAL_FAILED


class ExportConfigError(UserValueError):
    """Typed user error for exporter configuration errors."""

    error_code = ErrorCode.EXPORT_CONFIG


class IncludeError(UserValueError):
    """Typed user error for include/descriptor include errors."""

    error_code = ErrorCode.INCLUDE_ERROR


class MissingIncludeError(IncludeError, FileNotFoundError):
    """Keep missing-resource catch compatibility alongside the include identity."""


class GeneratorConfigError(UserValueError):
    """Typed user error for generator configuration errors."""

    error_code = ErrorCode.GENERATOR_CONFIG
    constructor_reason: str | None = None


class ConditionEvaluationError(UserValueError):
    """Typed user error for condition parsing/evaluation errors."""

    error_code = ErrorCode.CONDITION_EVAL_FAILED


class ParserValidationError(UserValueError):
    validation_errors: tuple[dict[str, object], ...] = ()

    """Typed user error for descriptor/parser validation failures."""

    error_code = ErrorCode.PARSER_VALIDATION


class MissingDescriptorError(ParserValidationError, FileNotFoundError):
    """Keep missing-resource catch compatibility alongside the parser identity."""


class ClientConfigError(UserValueError):
    """Typed user error for client configuration failures."""

    error_code = ErrorCode.CLIENT_CONFIG


class TaskConfigError(UserValueError):
    """Typed user error for task/statement configuration failures."""

    error_code = ErrorCode.TASK_CONFIG


class OperationError(UserRuntimeError):
    """Typed user error for operation execution failures."""

    error_code = ErrorCode.OPERATION_ERROR


class RuntimeConfigError(UserValueError):
    """Typed user error for runtime/platform configuration failures."""

    error_code = ErrorCode.RUNTIME_CONFIG


def is_user_error(err: BaseException) -> bool:
    return isinstance(err, (UserErrorBase, DomainError))


def _restore_user_error(
    error_type: type[UserErrorBase], message: str, state: _UserErrorState, cause: BaseException | None
) -> UserErrorBase:
    error = error_type(message)
    error.code = state["code"]
    error.issue_code = state["issue_code"]
    error.location = state["location"]
    if isinstance(error, InvalidDatasetError):
        error.dataset = state.get("dataset")
    if isinstance(error, MissingMemstoreProductError):
        error.product_type = state.get("product_type")
    if isinstance(error, ParserValidationError):
        error.validation_errors = state.get("validation_errors", ())
    if isinstance(error, GeneratorConfigError):
        error.constructor_reason = state.get("constructor_reason")
    error.__cause__ = cause
    return error


@dataclass(frozen=True)
class NormalizedDbError:
    """Passive native database facts; raw statements and driver messages stay private."""

    code: str | None
    category: str | None
    message: str

    def __str__(self) -> str:
        category = f" ({self.category})" if self.category else ""
        code = f" [{self.code}]" if self.code else ""
        return f"{self.message}{category}{code}"


class ExternalFailureCause(Exception):
    """Passive native cause classification for the private bounded-process transport."""

    def __init__(self, vendor_type: str, cause_types: tuple[str, ...]) -> None:
        super().__init__(vendor_type, cause_types)
        self.vendor_type = vendor_type
        self.cause_types = cause_types

    def __str__(self) -> str:
        return f"External operation failed ({self.vendor_type})"
