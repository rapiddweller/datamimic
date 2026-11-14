"""A generator that takes ``context`` draws from its own seeded stream (#473)."""

from pathlib import Path

from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.lifecycle import runner

_LIB = """
class CtxGen:
    def __init__(self, context):
        self.context = context

    def generate(self):
        return self.context.rng.randint(0, 999999999)
"""


def _rows(tmp_path: Path, name: str, setup_attrs: str, generate_attrs: str, keys: str) -> list[dict]:
    project = tmp_path / name
    project.mkdir()
    (project / "lib.scr.py").write_text(_LIB, encoding="utf-8")
    descriptor = project / "datamimic.xml"
    descriptor.write_text(
        f'<setup {setup_attrs}><execute uri="lib.scr.py"/>'
        f'<generate name="rows" count="4" {generate_attrs}>{keys}</generate></setup>',
        encoding="utf-8",
    )
    session = runner.create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True))
    captured = session.execute().captured
    assert captured is not None
    return captured["rows"]


_KEYS = "".join(f'<key name="{name}" generator="CtxGen(context=context)"/>' for name in "abc")


def test_three_generators_with_the_context_do_not_repeat_each_other(tmp_path: Path) -> None:
    rows = _rows(tmp_path, "one", 'rngSeed="473"', "", _KEYS)
    for row in rows:
        assert len({row["a"], row["b"], row["c"]}) == 3


def test_the_same_seed_replays_the_context_draws_and_another_seed_differs(tmp_path: Path) -> None:
    first = _rows(tmp_path, "first", 'rngSeed="473"', "", _KEYS)
    again = _rows(tmp_path, "again", 'rngSeed="473"', "", _KEYS)
    other = _rows(tmp_path, "other", 'rngSeed="474"', "", _KEYS)
    assert first == again
    assert first != other


def test_pages_of_one_generate_do_not_repeat_context_draws(tmp_path: Path) -> None:
    rows = _rows(tmp_path, "pages", 'rngSeed="473"', 'numProcess="2" pageSize="2"', _KEYS)
    draws = [row[name] for row in rows for name in "abc"]
    assert len(set(draws)) == len(draws)
