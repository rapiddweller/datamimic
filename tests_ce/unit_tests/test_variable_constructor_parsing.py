from datamimic_ce.engine.runtime.tasks.variable_task import _parse_constructor_string


def test_constructor_arguments_keep_literal_types_and_string_fallback():
    assert _parse_constructor_string("Person(code='0012', count=3, mode=fast)") == (
        "Person",
        {"code": "0012", "count": 3, "mode": "fast"},
    )
