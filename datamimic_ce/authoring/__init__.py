"""Canonical typed authoring API; concrete adapters are constructed lazily."""

from datamimic_ce.authoring.application.app import AuthoringApplication
from datamimic_ce.authoring.bootstrap import create_authoring_application

__all__ = ["AuthoringApplication", "create_authoring_application"]
