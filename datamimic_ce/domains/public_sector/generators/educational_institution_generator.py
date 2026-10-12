import datetime
import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import ClockAnchoredDomainGenerator
from datamimic_ce.domains.shared.generators.address_generator import AddressGenerator
from datamimic_ce.domains.shared.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.shared.literal_generators.contact.email_address_generator import EmailAddressGenerator


class EducationalInstitutionGenerator(ClockAnchoredDomainGenerator):
    """Generator for educational institution data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: datetime.datetime | None = None,
    ):
        """Initialize the educational institution generator.

        Args:
            dataset: The country code to use for data generation
            rng: Optional seeded random instance for deterministic output.
            reference_now: Optional fixed datetime anchor for deterministic mode.
        """
        super().__init__(dataset=dataset, rng=rng, reference_now=reference_now)
        # Derive deterministic RNG streams so seeded institutions keep nested contact details stable.
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        self._email_generator = EmailAddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        # Track last chosen level to reduce immediate repetition across entities
        self._last_level: str | None = None
        self._last_institution_type: str | None = None
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

    def generate_institution_id_candidate(self) -> str:
        rng = self.rng
        suffix = "".join(rng.choice("0123456789ABCDEF") for _ in range(8))
        return f"EDU-{suffix}"

    def generate_name(self, city: str, state: str, institution_type: str, level: str) -> str:
        if "University" in institution_type:
            name_formats = [
                f"{city} University",
                f"University of {city}",
                f"{state} State University",
                f"{city} Technical University",
                f"{city} Metropolitan University",
            ]
        elif "College" in institution_type:
            name_formats = [
                f"{city} College",
                f"{city} Community College",
                f"{state} College",
                f"{city} Technical College",
                f"{city} Liberal Arts College",
            ]
        elif "School" in institution_type:
            if "Elementary" in level:
                name_formats = [
                    f"{city} Elementary School",
                    f"{city} Primary School",
                    f"{city} Academy",
                    f"Washington Elementary School of {city}",
                    "Lincoln Elementary School",
                ]
            elif "Middle" in level:
                name_formats = [
                    f"{city} Middle School",
                    f"{city} Intermediate School",
                    f"{city} Junior High School",
                    "Jefferson Middle School",
                    "Roosevelt Middle School",
                ]
            elif "High" in level:
                name_formats = [
                    f"{city} High School",
                    f"{city} Senior High School",
                    f"{state} High School",
                    "Kennedy High School",
                    "Roosevelt High School",
                ]
            else:
                name_formats = [
                    f"{city} Academy",
                    f"{city} School",
                    f"{city} {level} School",
                    f"{state} Academy",
                    f"Central School of {city}",
                ]
        else:
            name_formats = [
                f"{city} Education Center",
                f"{city} Learning Institute",
                f"{city} Academy",
                f"{state} Institute",
                f"Central Institute of {city}",
            ]

        return self.rng.choice(name_formats)

    def generate_student_count(self, institution_type: str, level: str) -> int:
        rng = self.rng
        if "University" in institution_type:
            return rng.randint(5000, 40000)
        elif "College" in institution_type:
            return rng.randint(1000, 15000)
        elif "School" in institution_type:
            if "Elementary" in level:
                return rng.randint(200, 800)
            elif "Middle" in level:
                return rng.randint(300, 1000)
            elif "High" in level:
                return rng.randint(500, 2500)
            else:
                return rng.randint(200, 1500)
        else:
            return rng.randint(100, 5000)

    def generate_staff_count(self, student_count: int) -> int:
        student_to_staff_ratio = self.rng.uniform(10, 25)  # Average student-to-staff ratio
        return max(5, int(student_count / student_to_staff_ratio))

    #  centralize level picking so we can avoid immediate repetition while
    # staying dataset-driven. The model calls into this helper.
    def pick_level(self, institution_type: str, *, start: Path) -> str:
        import csv

        from datamimic_ce.domains.domain_core.datasets.path import dataset_path
        from datamimic_ce.domains.shared.datasets.loader import pick_one_weighted_no_repeat

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
            values, weights = zip(*items, strict=True)
            return pick_one_weighted_no_repeat(self._rng, list(values), list(weights), last=self._last_level)

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
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

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
        from datamimic_ce.domains.shared.datasets.loader import (
            load_weighted_values_try_dataset,
            pick_one_weighted_no_repeat,
        )

        values, weights = load_weighted_values_try_dataset(
            "public_sector", "education", "institution_types.csv", dataset=self._dataset, start=start
        )
        choice = pick_one_weighted_no_repeat(self._rng, values, weights, last=self._last_institution_type)
        self._last_institution_type = choice
        return choice

    def generate_programs(self, level: str, *, start: Path) -> list[str]:
        if "Elementary" in level:
            slug = "elementary"
        elif "Middle" in level:
            slug = "middle_school"
        elif "High" in level:
            slug = "high_school"
        elif any(k in level for k in ("Higher", "Undergraduate", "Graduate", "Postgraduate")):
            slug = "higher_education"
        elif any(k in level for k in ("Vocational", "Technical")):
            slug = "vocational"
        else:
            slug = "k12"

        return self.pick_programs(slug, start=start)

    # Helper: programs selection, weighted without replacement
    def pick_programs(self, slug: str, *, start: Path) -> list[str]:
        from datamimic_ce.domains.shared.datasets.loader import (
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
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

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
        all_fac = list(dict.fromkeys(list(common_vals) + list(spec_vals)))
        k = self._rng.randint(5, min(15, len(all_fac)))
        return sorted(self._rng.sample(all_fac, k))
