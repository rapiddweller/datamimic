# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support: info@rapiddweller.com

"""Registry for built-in DSL-exposable literal generators."""

from __future__ import annotations

_REGISTRY: dict[str, type] = {}
_LOADED = False


def _ensure_loaded() -> None:
    global _LOADED
    if not _LOADED:
        auto_register_generators()
        _LOADED = True


def auto_register_generators() -> None:
    """Register the built-in literal generators used by DSL expressions."""
    for generator in _builtin_generators():
        _REGISTRY.setdefault(generator.__name__, generator)


def _builtin_generators() -> tuple[type, ...]:
    # Keep module order and class names explicit: this is the complete built-in DSL inventory.
    from datamimic_ce.domains.shared.literal_generators.academic_title_generator import AcademicTitleGenerator
    from datamimic_ce.domains.shared.literal_generators.binary_generator import BinaryGenerator
    from datamimic_ce.domains.shared.literal_generators.birthdate_generator import BirthdateGenerator
    from datamimic_ce.domains.shared.literal_generators.boolean_generator import BooleanGenerator
    from datamimic_ce.domains.shared.literal_generators.cnpj_generator import CNPJGenerator
    from datamimic_ce.domains.shared.literal_generators.color_generators import ColorGenerator
    from datamimic_ce.domains.shared.literal_generators.company_name_generator import CompanyNameGenerator
    from datamimic_ce.domains.shared.literal_generators.cpf_generator import CPFGenerator
    from datamimic_ce.domains.shared.literal_generators.data_faker_generator import DataFakerGenerator
    from datamimic_ce.domains.shared.literal_generators.datetime_generator import DateTimeGenerator
    from datamimic_ce.domains.shared.literal_generators.department_name_generator import DepartmentNameGenerator
    from datamimic_ce.domains.shared.literal_generators.domain_generator import DomainGenerator
    from datamimic_ce.domains.shared.literal_generators.ean_generator import EANGenerator
    from datamimic_ce.domains.shared.literal_generators.email_address_generator import EmailAddressGenerator
    from datamimic_ce.domains.shared.literal_generators.family_name_generator import FamilyNameGenerator
    from datamimic_ce.domains.shared.literal_generators.float_generator import FloatGenerator
    from datamimic_ce.domains.shared.literal_generators.gender_generator import GenderGenerator
    from datamimic_ce.domains.shared.literal_generators.given_name_generator import GivenNameGenerator
    from datamimic_ce.domains.shared.literal_generators.global_increment_generator import GlobalIncrementGenerator
    from datamimic_ce.domains.shared.literal_generators.hash_generator import HashGenerator
    from datamimic_ce.domains.shared.literal_generators.increment_generator import IncrementGenerator
    from datamimic_ce.domains.shared.literal_generators.integer_generator import IntegerGenerator
    from datamimic_ce.domains.shared.literal_generators.nobility_title_generator import NobilityTitleGenerator
    from datamimic_ce.domains.shared.literal_generators.password_generator import PasswordGenerator
    from datamimic_ce.domains.shared.literal_generators.phone_number_generator import PhoneNumberGenerator
    from datamimic_ce.domains.shared.literal_generators.prefixed_id_generator import PrefixedIdGenerator
    from datamimic_ce.domains.shared.literal_generators.sector_generator import SectorGenerator
    from datamimic_ce.domains.shared.literal_generators.ssn_generator import SSNGenerator
    from datamimic_ce.domains.shared.literal_generators.state_transition_generator import StateTransitionGenerator
    from datamimic_ce.domains.shared.literal_generators.street_name_generator import StreetNameGenerator
    from datamimic_ce.domains.shared.literal_generators.string_generator import StringGenerator
    from datamimic_ce.domains.shared.literal_generators.token_generator import TokenGenerator
    from datamimic_ce.domains.shared.literal_generators.url_generator import UrlGenerator
    from datamimic_ce.domains.shared.literal_generators.uuid_generator import UUIDGenerator

    return (
        AcademicTitleGenerator, BinaryGenerator, BirthdateGenerator, BooleanGenerator, CNPJGenerator,
        ColorGenerator, CompanyNameGenerator, CPFGenerator, DataFakerGenerator, DateTimeGenerator,
        DepartmentNameGenerator, DomainGenerator, EANGenerator, EmailAddressGenerator, FamilyNameGenerator,
        FloatGenerator, GenderGenerator, GivenNameGenerator, GlobalIncrementGenerator, HashGenerator,
        IncrementGenerator, IntegerGenerator, NobilityTitleGenerator, PasswordGenerator,
        PhoneNumberGenerator, PrefixedIdGenerator, SectorGenerator, SSNGenerator, StateTransitionGenerator,
        StreetNameGenerator, StringGenerator, TokenGenerator, UrlGenerator, UUIDGenerator,
    )


def generator_namespace() -> dict[str, type]:
    """Return the built-in generator namespace for DSL and custom-script use."""
    _ensure_loaded()
    return dict(_REGISTRY)
