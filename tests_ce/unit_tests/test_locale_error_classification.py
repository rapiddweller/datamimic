import pytest

from datamimic_ce.domains.shared import locales
from datamimic_ce.domains.shared.services import address_api
from datamimic_ce.errors import InvalidLocaleError


def test_loader_marks_only_unsupported_dataset_as_locale_error() -> None:
    with pytest.raises(locales.UnsupportedLocaleDatasetError) as caught:
        locales.load_locale("xx_XX", "v1")

    assert caught.value.locale == "xx_XX"
    assert caught.value.dataset == "XX"


def test_unsupported_version_is_not_an_invalid_locale() -> None:
    with pytest.raises(ValueError, match="Unsupported locale version") as caught:
        locales.load_locale("en_US", "v2")

    assert not isinstance(caught.value, locales.UnsupportedLocaleDatasetError)


def test_missing_locale_data_is_not_reclassified_as_invalid_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_person_data(dataset: str) -> object:
        raise FileNotFoundError(f"missing {dataset}")

    monkeypatch.setattr(locales, "_load_person_locale", missing_person_data)
    locales.load_locale.cache_clear()
    with pytest.raises(ValueError, match="missing required files") as source_error:
        locales.load_locale("en_US", "v1")
    assert not isinstance(source_error.value, locales.UnsupportedLocaleDatasetError)

    def missing_locale(locale: str, version: str) -> locales.LocalePack:
        raise source_error.value

    monkeypatch.setattr(address_api, "load_locale", missing_locale)
    with pytest.raises(ValueError, match="missing required files") as api_error:
        address_api.generate(address_api.AddressRequest())
    assert not isinstance(api_error.value, InvalidLocaleError)
