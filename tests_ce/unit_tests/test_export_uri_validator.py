import pytest

from datamimic_ce.model.model_util import ModelUtil


def test_normalize_strips_slashes_and_passes_a_valid_prefix():
    assert ModelUtil.normalize_export_uri("reports/2026") == "reports/2026"
    assert ModelUtil.normalize_export_uri("/a/b/") == "a/b"
    assert ModelUtil.normalize_export_uri(None) is None


@pytest.mark.parametrize(
    "bad,msg",
    [
        ("  ", r"empty|whitespace"),
        (" x", r"whitespace"),
        ("s3://b", r"URL"),
        ("a\\b", r"backslash"),
        ("a/../b", r"traverse"),
        ("a\tb", r"control"),
    ],
)
def test_normalize_rejects_bad_prefixes(bad, msg):
    with pytest.raises(ValueError, match=msg):
        ModelUtil.normalize_export_uri(bad)
