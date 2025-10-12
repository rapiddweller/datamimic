import pytest
from datamimic_ce.utils.xml_util import safe_parse_generator_param

@pytest.mark.parametrize("input_str,expected", [
    # Valid literals
    ("[0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]", [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]),
    ("[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ("[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]", [1] + [0]*59), # Test with a list that sums to 60 elements
    ("{0: 0.2, 1: 0.2, 2: 0.2}", {0: 0.2, 1: 0.2, 2: 0.2}),
    ("'simple string'", 'simple string'),
    ("42", 42),
    ("3.14", 3.14),
    ("True", True),
    ("False", False),
    ("None", None),

    # XML escaped strings that evaluate to literals
    ("&quot;[1,2,3]&quot;", [1,2,3]),
    ("&quot;{\'a\': 1}&quot;", {'a': 1}),
    ("&quot;test string&quot;", "test string"), # This should become "test string"
    ("'[1,2,3]'", [1,2,3]), # String literal containing a list representation

    # Strings that are not valid literals (should be returned as is after unescaping)
    ("[0.2]*6 + [0.02]*18", "[0.2]*6 + [0.02]*18"), # Python expression, not a literal
    ("[1 if m in (0,15,30,45) else 0 for m in range(60)]", "[1 if m in (0,15,30,45) else 0 for m in range(60)]"), # List comprehension
    ("not_a_list_or_dict", "not_a_list_or_dict"),
    ("", ""), # Empty string
    ("&quot;&quot;", ""), # Empty string, XML escaped
    ("  [1,2,3]  ", [1,2,3]), # Whitespace around literal
    ("&quot;  [1,2,3]  &quot;", [1,2,3]), # Whitespace with XML escaping

    # Test cases for nested string literals
    ("'\"[1,2,3]\"'", "[1,2,3]"), # String literal containing an escaped string literal of a list
    ("\"'[1,2,3]'\"", "[1,2,3]"), # String literal containing an escaped string literal of a list

    # Test cases from previous failures or edge cases
    ("None", None),
    ("\"None\"", None), # String "None" should evaluate to None object
    ("&quot;None&quot;", None), # XML escaped string "None" should evaluate to None object
    ("True", True),
    ("\"True\"", True), # String "True" should evaluate to True object
    ("&quot;True&quot;", True), # XML escaped string "True" should evaluate to True object
    ("1", 1),
    ("\"1\"", 1), # String "1" should evaluate to int 1
    ("&quot;1&quot;", 1), # XML escaped string "1" should evaluate to int 1
    ("[]", []),
    ("\"[]\"", []),
    ("&quot;[]&quot;", []),
    ("{}", {}),
    ("\"{}\"", {}),
    ("&quot;{}&quot;", {}),
])
def test_safe_parse_generator_param(input_str, expected):
    result = safe_parse_generator_param(input_str)
    assert result == expected


def test_safe_parse_generator_param_invalid():
    # Should return the string itself if not a valid literal
    assert safe_parse_generator_param("not_a_list_or_dict") == "not_a_list_or_dict"
    # Should handle XML entities for plain strings
    assert safe_parse_generator_param("&quot;test&quot;") == "test"
    assert safe_parse_generator_param("&lt;tag&gt;") == "<tag>"
    assert safe_parse_generator_param("plain string with &amp; ampersand") == "plain string with & ampersand"
