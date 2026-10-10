from __future__ import annotations

from enum import Enum


class DomainErrorCode(str, Enum):
    INVALID_REQUEST = "invalid_request"
    INVALID_COUNT = "invalid_count"
    INVALID_CONSTRAINTS = "invalid_constraints"
    INVALID_COMPONENT_CONSTRAINTS = "invalid_component_constraints"
    INVALID_COMPONENT_ID = "invalid_component_id"
    INVALID_PROFILE_ID = "invalid_profile_id"
    INVALID_PROFILE_SELECTOR = "invalid_profile_selector"
    MISSING_COMPONENT_DATASET = "missing_component_dataset"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    UNKNOWN_COMPONENT = "unknown_component"
    UNKNOWN_PROFILE = "unknown_profile"
    UNSUPPORTED_DOMAIN = "unsupported_domain"
    UNSUPPORTED_COMPONENT_DATASET = "unsupported_component_dataset"
    UNSUPPORTED_COMPONENT_VERSION = "unsupported_component_version"

class ErrorCode(str, Enum):
    INVALID_LOCALE = "E002"
