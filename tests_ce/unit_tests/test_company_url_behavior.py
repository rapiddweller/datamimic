from __future__ import annotations

from hashlib import sha256
from random import Random

from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.shared.generators.company_generator import CompanyGenerator
from datamimic_ce.domains.shared.models.company import Company


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _ChoiceRandom(Random):
    def __init__(self, schemes: list[str], events: list[object]) -> None:
        super().__init__(152)
        self.schemes = list(schemes)
        self.events = events
        self.choices: list[list[str]] = []

    def choice(self, seq):
        values = list(seq)
        self.events.append(("choice", values))
        self.choices.append(values)
        super().choice(seq)
        return self.schemes.pop(0)


class _ObservedCompanyGenerator(CompanyGenerator):
    def __init__(self, rng: Random, events: list[object]) -> None:
        self.events = events
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng


def _traced_company(generator: CompanyGenerator, events: list[object], short_name: str = "Acme Corp") -> Company:
    class TracedCompany(Company):
        @property
        @property_cache
        def email(self) -> str:
            events.append("email")
            return super().email

    company = TracedCompany(generator)
    company.field_cache["short_name"] = short_name
    return company


def test_url_draws_scheme_before_lazy_email_and_caches_result(monkeypatch) -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["https"], events)
    generator = _ObservedCompanyGenerator(rng, events)
    company = _traced_company(generator, events)

    def generate_email(company_name: str) -> str:
        events.append(("generate_email", company_name))
        return "support@acme.test"

    generator.email_address_generator.generate_with_company_name = generate_email

    assert company.url == "https://acme.test"
    assert events == ["rng", ("choice", ["http", "https"]), "email", ("generate_email", "Acme Corp")]
    assert rng.choices == [["http", "https"]]
    assert generator.rng_reads == 1
    assert company.url == "https://acme.test"
    assert company.email == "support@acme.test"
    assert len(events) == 4
    assert generator.rng_reads == 1


def test_email_failure_after_scheme_draw_leaves_url_uncached_and_retries_without_rng_rollback() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["http", "https"], events)
    generator = _ObservedCompanyGenerator(rng, events)
    company = _traced_company(generator, events)
    initial_state = rng.getstate()
    calls = 0

    def fail_once(company_name: str) -> str:
        nonlocal calls
        calls += 1
        events.append(("generate_email", company_name))
        if calls == 1:
            raise RuntimeError("scripted company email failure")
        return "support@acme.test"

    generator.email_address_generator.generate_with_company_name = fail_once

    try:
        _ = company.url
    except RuntimeError as error:
        assert str(error) == "scripted company email failure"
    else:
        raise AssertionError("expected the email failure")
    assert "url" not in company.field_cache
    assert "email" not in company.field_cache
    assert rng.getstate() != initial_state
    state_after_failure = rng.getstate()

    assert company.url == "https://acme.test"
    assert company.url == "https://acme.test"
    assert "url" in company.field_cache
    assert company.email == "support@acme.test"
    assert rng.getstate() != state_after_failure
    assert rng.choices == [["http", "https"], ["http", "https"]]
    assert generator.rng_reads == 2
    assert calls == 2
    assert events == [
        "rng",
        ("choice", ["http", "https"]),
        "email",
        ("generate_email", "Acme Corp"),
        "rng",
        ("choice", ["http", "https"]),
        "email",
        ("generate_email", "Acme Corp"),
    ]


def test_public_rng_override_is_used_for_url_scheme() -> None:
    events: list[object] = []
    private_rng = Random(100)
    public_rng = _ChoiceRandom(["https"], events)

    class PublicRngCompanyGenerator(_ObservedCompanyGenerator):
        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            events.append("public_rng")
            return public_rng

    generator = PublicRngCompanyGenerator(private_rng, events)
    company = _traced_company(generator, events)
    generator.email_address_generator.generate_with_company_name = lambda name: "help@acme.test"
    private_state = private_rng.getstate()

    assert company.url == "https://acme.test"
    assert private_rng.getstate() == private_state
    assert public_rng.choices == [["http", "https"]]
    assert generator.rng_reads == 1
    assert events[:2] == ["public_rng", ("choice", ["http", "https"])]


def test_seeded_url_first_and_email_first_keep_values_and_rng_states() -> None:
    url_first_rng = Random(152)
    url_first_generator = CompanyGenerator(dataset="US", rng=url_first_rng)
    url_first = Company(url_first_generator)
    url_first.field_cache["short_name"] = "Acme Corp"
    assert _fingerprint(url_first_rng) == "d388eb52e658ed4f2c49b7dc1cc770986cfe56f8c014461509e000a6ebd770cf"
    assert _fingerprint(url_first_generator.email_address_generator.rng) == (
        "c815ab9e33d65b695dced933c88bbcb81899a0b4725c9df56e402bb5012c1eae"
    )
    assert url_first.url == "http://chofsauqd.com"
    assert url_first.email == "kevinmiller@chofsauqd.com"
    assert _fingerprint(url_first_rng) == "b701af4e52f2c53ee5c2bc045090a2aef98a1508fd107fa78f78a70328636be8"
    assert _fingerprint(url_first_generator.email_address_generator.rng) == (
        "bf5256436ae1e45226e93577e51aeb57c850feb5f1b776070f1e9029131d7498"
    )
    assert _fingerprint(url_first_generator.email_address_generator._domain_generator.rng) == (
        "d954b19eae49530e156de42f071b062fa1281865e0a86bc693f2b17b0dfcec29"
    )

    email_first_rng = Random(152)
    email_first_generator = CompanyGenerator(dataset="US", rng=email_first_rng)
    email_first = Company(email_first_generator)
    email_first.field_cache["short_name"] = "Acme Corp"
    assert email_first.email == "kevinmiller@chofsauqd.com"
    assert email_first.url == "http://chofsauqd.com"
    assert _fingerprint(email_first_rng) == "b701af4e52f2c53ee5c2bc045090a2aef98a1508fd107fa78f78a70328636be8"
    assert _fingerprint(email_first_generator.email_address_generator.rng) == (
        "bf5256436ae1e45226e93577e51aeb57c850feb5f1b776070f1e9029131d7498"
    )
    assert _fingerprint(email_first_generator.email_address_generator._domain_generator.rng) == (
        "d954b19eae49530e156de42f071b062fa1281865e0a86bc693f2b17b0dfcec29"
    )


def test_shared_generator_companies_keep_url_and_email_caches_per_entity() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["http", "https"], events)
    generator = _ObservedCompanyGenerator(rng, events)
    first = _traced_company(generator, events, "First Co")
    second = _traced_company(generator, events, "Second Co")
    email_calls: list[str] = []

    def generate_email(company_name: str) -> str:
        email_calls.append(company_name)
        return f"support@{company_name.split()[0].lower()}.test"

    generator.email_address_generator.generate_with_company_name = generate_email

    assert first.url == "http://first.test"
    assert second.url == "https://second.test"
    assert first.url == "http://first.test"
    assert second.url == "https://second.test"
    assert first.email == "support@first.test"
    assert second.email == "support@second.test"
    assert email_calls == ["First Co", "Second Co"]
    assert len(rng.choices) == 2
    assert generator.rng_reads == 2


def test_company_url_delegates_scheme_selection_before_lazy_email() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["https"], events)

    class CandidateCompanyGenerator(_ObservedCompanyGenerator):
        def generate_url_scheme(self) -> str:
            events.append("generate_url_scheme")
            return self.rng.choice(["http", "https"])

    generator = CandidateCompanyGenerator(rng, events)
    company = _traced_company(generator, events)

    def generate_email(company_name: str) -> str:
        events.append(("generate_email", company_name))
        return "support@acme.test"

    generator.email_address_generator.generate_with_company_name = generate_email

    assert company.url == "https://acme.test"
    assert events == [
        "generate_url_scheme",
        "rng",
        ("choice", ["http", "https"]),
        "email",
        ("generate_email", "Acme Corp"),
    ]
    assert generator.rng_reads == 1


def test_generator_scheme_method_uses_public_rng_choice_once() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["https"], events)
    generator = _ObservedCompanyGenerator(rng, events)

    assert generator.generate_url_scheme() == "https"
    assert events == ["rng", ("choice", ["http", "https"])]
    assert generator.rng_reads == 1
    assert rng.choices == [["http", "https"]]
