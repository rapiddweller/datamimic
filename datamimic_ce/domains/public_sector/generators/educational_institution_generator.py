import random
from pathlib import Path

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator


class EducationalInstitutionGenerator(BaseDomainGenerator):
    """Generator for educational institution data."""

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the educational institution generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = (dataset or "US").upper()  #  share a normalized dataset across all child generators
        self._rng = rng or random.Random()  #  deterministic RNG injection point
        # Derive deterministic RNG streams so seeded institutions keep nested contact details stable.
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._email_generator = EmailAddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        # Track last chosen level to reduce immediate repetition across entities
        self._last_level: str | None = None
        self._last_accreditations: tuple[str, ...] | None = None

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    @property
    def email_generator(self) -> EmailAddressGenerator:
        return self._email_generator

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Fork deterministic child RNGs so seeded institutions replay without cross-coupling randomness.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    #  centralize level picking so we can avoid immediate repetition while
    # staying dataset-driven. The model calls into this helper.
    def pick_level(self, institution_type: str, *, start: Path) -> str:
        import csv

        from datamimic_ce.domains.utils.dataset_path import dataset_path

        path = dataset_path("public_sector", "education", f"levels_{self._dataset}.csv", start=start)
        levels_by_pattern: dict[str, list[tuple[str, float]]] = {}
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                if not r:
                    continue
                pattern, value, weight = r[0], r[1], float(r[2]) if len(r) > 2 else 1.0
                levels_by_pattern.setdefault(pattern, []).append((value, weight))

        def pick_for(pattern: str) -> str | None:
            items = levels_by_pattern.get(pattern)
            if not items:
                return None
            # Avoid immediate repetition when possible
            if self._last_level and len(items) > 1:
                pool = [(v, w) for (v, w) in items if v != self._last_level]
                values, weights = zip(*pool, strict=False)
            else:
                values, weights = zip(*items, strict=False)
            return self._rng.choices(list(values), weights=list(weights), k=1)[0]

        for patt in ("University", "College", "Vocational", "Special", "School"):
            if patt in institution_type:
                chosen = pick_for(patt)
                if chosen:
                    self._last_level = chosen
                    return chosen

        chosen = pick_for("Default") or "Higher Education"
        self._last_level = chosen
        return chosen

    def pick_accreditations(self, institution_type: str, *, start: Path) -> list[str]:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        # Select appropriate accreditations based on institution type
        if any(k in institution_type for k in ("University", "College")):
            cat = "higher_ed"
        elif any(k in institution_type for k in ("Vocational", "Technical")):
            cat = "vocational"
        else:
            cat = "k12"

        values, _ = load_weighted_values_try_dataset(
            "public_sector", "education", f"accreditations_{cat}.csv", dataset=self._dataset, start=start
        )
        k = self._rng.randint(1, min(3, len(values)))
        chosen = sorted(values) if k >= len(values) else sorted(self._rng.sample(values, k))
        # Avoid repeating the exact same set in successive calls when possible
        as_tuple = tuple(chosen)
        if self._last_accreditations is not None and as_tuple == self._last_accreditations and len(values) > 1:
            # Attempt one alternate draw
            pool = [v for v in values if v not in chosen]
            if pool:
                # swap one element
                chosen[-1] = self._rng.choice(pool)
                chosen = sorted(chosen)
                as_tuple = tuple(chosen)
        self._last_accreditations = as_tuple
        return chosen

    # Helper: pick institution type from dataset with weighted values
    def pick_institution_type(self, *, start: Path) -> str:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted

        values, weights = load_weighted_values_try_dataset(
            "public_sector", "education", "institution_types.csv", dataset=self._dataset, start=start
        )
        choice = pick_one_weighted(self._rng, values, weights)
        last = getattr(self, "_last_institution_type", None)
        if last == choice and len(values) > 1:
            choice = pick_one_weighted(self._rng, values, weights)
        self._last_institution_type = choice
        return choice

    # Helper: programs selection, weighted without replacement
    def pick_programs(self, slug: str, *, start: Path) -> list[str]:
        from datamimic_ce.domains.utils.dataset_loader import (
            load_weighted_values_try_dataset,
            sample_weighted_no_replacement,
        )

        values, w = load_weighted_values_try_dataset(
            "public_sector", "education", f"programs_{slug}.csv", dataset=self._dataset, start=start
        )
        k = self._rng.randint(3, min(10, len(values)))
        if k >= len(values):
            return sorted(values)
        selected = sample_weighted_no_replacement(self._rng, values, [float(x) for x in w], k)
        return sorted(selected)

    # Helper: facilities selection based on type
    def pick_facilities(self, institution_type: str, *, start: Path) -> list[str]:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        if any(k in institution_type for k in ("University", "College")):
            cat = "higher_ed"
        elif any(k in institution_type for k in ("Vocational", "Technical")):
            cat = "vocational"
        else:
            cat = "k12"
        common_vals, _ = load_weighted_values_try_dataset(
            "public_sector", "education", "facilities_common.csv", dataset=self._dataset, start=start
        )
        spec_vals, _ = load_weighted_values_try_dataset(
            "public_sector", "education", f"facilities_{cat}.csv", dataset=self._dataset, start=start
        )
        all_fac = list(set(list(common_vals) + list(spec_vals)))
        k = self._rng.randint(5, min(15, len(all_fac)))
        return sorted(self._rng.sample(all_fac, k))
