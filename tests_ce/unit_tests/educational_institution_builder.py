"""Seeded educational institution builder shared by the institution behavior tests."""

from random import Random

from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution


def build_institution(seed: int) -> tuple[EducationalInstitution, EducationalInstitutionGenerator, Random]:
    rng = Random(seed)
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    return EducationalInstitution(generator), generator, rng
