"""Shared user-facing error types."""

from datamimic_ce.errors.base import DomainError
from datamimic_ce.errors.codes import DomainErrorCode

__all__ = ["DomainError", "DomainErrorCode"]
