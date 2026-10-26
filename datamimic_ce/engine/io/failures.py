# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Reduce driver and parser causes to passive facts only at the bounded IPC boundary."""

from zipfile import BadZipFile

from lxml.etree import Error as LxmlError
from pymongo.errors import PyMongoError
from sqlalchemy.exc import SQLAlchemyError

from datamimic_ce.errors import ExternalFailureCause


def normalize_error_cause_for_transport(error: BaseException) -> None:
    """The single-use child owns this error; normal runtime causes stay native."""
    current = error
    seen = {id(error)}
    while current.__cause__ is not None:
        cause = current.__cause__
        if id(cause) in seen:
            return
        seen.add(id(cause))
        # lxml errors do not pickle; a BadZipFile from an invalid .xlsx is no passive value either.
        if isinstance(cause, (SQLAlchemyError, PyMongoError, LxmlError, BadZipFile)):
            cause_types: list[str] = []
            nested: BaseException | None = cause
            vendor_seen: set[int] = set()
            while nested is not None and id(nested) not in vendor_seen and len(cause_types) < 16:
                vendor_seen.add(id(nested))
                cause_types.append(f"{type(nested).__module__}.{type(nested).__name__}")
                nested = nested.__cause__
            fact = ExternalFailureCause(cause_types[0], tuple(cause_types))
            object.__setattr__(current, "__cause__", fact)
            return
        current = cause
