# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datetime import datetime
from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field

PERSON_SCHEMA = EntitySchema(
    "Person",
    (
        field("birthdate", datetime, "Date of birth."),
        field("given_name", str, "First (given) name."),
        field("family_name", str, "Last (family) name."),
        field("full_name", str, "Full display name."),
        field("gender", str, "Gender."),
        field("name", str, "Name with titles and salutation."),
        field("age", int, "Age in years."),
        field("email", str, "Primary email address."),
        field("phone", str, "Landline phone number."),
        field("mobile_phone", str, "Mobile phone number."),
        field("academic_title", str, "Academic title, if any.", optional=True),
        field("salutation", str, "Salutation form."),
        field("nobility_title", str, "Nobility title, if any.", optional=True),
        field("transaction_profile", (str, dict), "Spending/transaction behaviour profile.", optional=True),
    ),
)


class PersonService(BaseDomainService[Person]):
    """Service for managing person data.

    This class provides methods for creating, retrieving, and managing person data.
    """

    def __init__(
        self,
        dataset: str | None = None,
        min_age: int = 18,
        max_age: int = 65,
        female_quota: float = 0.5,
        other_gender_quota: float = 0.0,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
        noble_quota: float = 0.001,
        academic_title_quota: float = 0.5,
    ):
        resolved_config = (demographic_config or DemographicConfig()).with_defaults(
            default_age_min=min_age,
            default_age_max=max_age,
        )
        # Bridge int | None -> int for the generator (with_defaults already filled these).
        min_age_resolved = resolved_config.age_min if resolved_config.age_min is not None else min_age
        max_age_resolved = resolved_config.age_max if resolved_config.age_max is not None else max_age
        super().__init__(
            PersonGenerator(
                dataset=dataset,
                min_age=min_age_resolved,
                max_age=max_age_resolved,
                female_quota=female_quota,
                other_gender_quota=other_gender_quota,
                demographic_config=resolved_config,
                # Pass sampler through the service so entity generation can honour population priors.
                demographic_sampler=demographic_sampler,
                rng=rng,
                # Thread descriptor-level overrides for noble/title quotas into the generator for determinism.
                noble_quota=noble_quota,
                academic_title_quota=academic_title_quota,
            ),
            Person,
        )

    DATASET_PATTERNS = (
        "common/person/givenName_male_{CC}.csv",
        "common/person/givenName_female_{CC}.csv",
        "common/person/familyName_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return PERSON_SCHEMA.fields
