from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.statement import Statement


def test_root_generate_lookup_stops_at_setup_and_finds_enclosing_generate() -> None:
    setup = Statement(None, None)
    generate = object.__new__(GenerateStatement)
    Statement.__init__(generate, "outer", setup)
    child = Statement("leaf", generate)

    assert setup.get_root_generate_statement() is None
    assert generate.get_root_generate_statement() is None
    assert child.get_root_generate_statement() is generate
