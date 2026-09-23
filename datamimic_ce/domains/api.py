"""Public domain generator types and capability projection."""

from collections.abc import Iterator

from datamimic_ce.domains.common.demographics.loader import load_demographic_profile
from datamimic_ce.domains.common.demographics.profile import DemographicProfileId
from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.literal_generators.increment_generator import IncrementGenerator
from datamimic_ce.domains.common.literal_generators.number_sequences import finite_number_sequence_capacity
from datamimic_ce.domains.common.literal_generators.state_transition_generator import (
    StateMachineDef,
    StateTransitionGenerator,
)
from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.common.sampling import cumulated_index
from datamimic_ce.domains.converters.append_converter import AppendConverter
from datamimic_ce.domains.converters.converter import Converter
from datamimic_ce.domains.converters.custom_converter import CustomConverter
from datamimic_ce.domains.converters.cut_length_converter import CutLengthConverter
from datamimic_ce.domains.converters.date2timestamp_converter import Date2TimestampConverter
from datamimic_ce.domains.converters.date_format_converter import DateFormatConverter
from datamimic_ce.domains.converters.hash_converter import HashConverter
from datamimic_ce.domains.converters.java_hash_converter import JavaHashConverter
from datamimic_ce.domains.converters.lower_case_converter import LowerCaseConverter
from datamimic_ce.domains.converters.mask_converter import MaskConverter
from datamimic_ce.domains.converters.middle_mask_converter import MiddleMaskConverter
from datamimic_ce.domains.converters.remove_none_or_empty_element_converter import RemoveNoneOrEmptyElementConverter
from datamimic_ce.domains.converters.substring_converter import SubstringConverter
from datamimic_ce.domains.converters.timestamp2date_converter import Timestamp2DateConverter
from datamimic_ce.domains.converters.upper_case_converter import UpperCaseConverter
from datamimic_ce.domains.determinism import get_datamimic_lib_version
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.domain_core.entity_registry import EntitySpec, get_entity_service_class, list_entity_specs
from datamimic_ce.domains.domain_core.generator_registry import generator_namespace
from datamimic_ce.domains.domain_core.runtime.clock import from_epoch_utc, resolve_clock, to_epoch_utc
from datamimic_ce.domains.domain_core.runtime.rng import derive_child_seed, spawn_rng
from datamimic_ce.domains.domain_core.runtime.run_seed import RunSeed
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount
from datamimic_ce.domains.finance.models.transaction import Transaction
from datamimic_ce.domains.healthcare.services.patient_service import PatientService
from datamimic_ce.domains.utils.random_source import RandomSource
from datamimic_ce.domains.utils.rng_uuid import uuid4_from_random
from datamimic_ce.engine.dsl.api import GeneratorCapability, describe_generator_type


def iter_generator_types() -> Iterator[type]:
    """Iterate the literal-generator classes available to runtime orchestration."""
    yield from generator_namespace().values()


def iter_generator_capabilities() -> Iterator[GeneratorCapability]:
    for generator_type in iter_generator_types():
        yield describe_generator_type(generator_type)


__all__ = [
    "AppendConverter",
    "BaseDomainGenerator",
    "BaseLiteralGenerator",
    "BankAccount",
    "Converter",
    "CustomConverter",
    "CutLengthConverter",
    "Date2TimestampConverter",
    "DateFormatConverter",
    "DemographicConfig",
    "DemographicProfileId",
    "DemographicSampler",
    "EntitySpec",
    "HashConverter",
    "JavaHashConverter",
    "LowerCaseConverter",
    "MaskConverter",
    "MiddleMaskConverter",
    "PatientService",
    "RemoveNoneOrEmptyElementConverter",
    "RunSeed",
    "RandomSource",
    "StateMachineDef",
    "StateTransitionGenerator",
    "StringGenerator",
    "SubstringConverter",
    "Timestamp2DateConverter",
    "Transaction",
    "TransactionGenerator",
    "UpperCaseConverter",
    "cumulated_index",
    "derive_child_seed",
    "finite_number_sequence_capacity",
    "from_epoch_utc",
    "get_datamimic_lib_version",
    "get_entity_service_class",
    "iter_generator_capabilities",
    "iter_generator_types",
    "list_entity_specs",
    "load_demographic_profile",
    "resolve_clock",
    "spawn_rng",
    "to_epoch_utc",
    "uuid4_from_random",
    "IncrementGenerator",
]
