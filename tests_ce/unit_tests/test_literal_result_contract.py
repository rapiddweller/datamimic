from random import Random
from types import SimpleNamespace
from typing import get_type_hints

import numpy
import pytest

from datamimic_ce.domains.api import BaseLiteralGenerator, StringGenerator
from datamimic_ce.domains.shared.literal_generators.primitives.data_faker_generator import DataFakerGenerator
from datamimic_ce.engine.dsl.api import KeyStatement
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.runtime.tasks.values.construction.factory import GeneratorUtil
from datamimic_ce.engine.runtime.tasks.values.scalar.key_task import KeyTask


class NativeGenerator(BaseLiteralGenerator):
    def __init__(self, value: object, error: Exception | None = None) -> None:
        super().__init__(rng=Random(7))
        self.value = value
        self.error = error
        self.calls = 0

    def generate(self) -> object:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.value


def _task(generator: NativeGenerator, mode: str) -> KeyTask:
    task = KeyTask.__new__(KeyTask)
    task._statement = KeyStatement(KeyModel(name="native", generator="NativeGenerator"), None)
    task._mode = mode
    task._generator = generator
    task._pagination = None
    return task


@pytest.mark.parametrize("mode", [KeyTask._GENERATOR_MODE, KeyTask._LAZY_GENERATOR_MODE])
@pytest.mark.parametrize("value", [object(), None, {"cells": [object(), None]}], ids=["sentinel", "none", "native-map"])
def test_native_generator_value_path_preserves_identity_and_one_call(
    monkeypatch: pytest.MonkeyPatch, mode: str, value: object
) -> None:
    generator = NativeGenerator(value)
    task = _task(generator, mode)
    monkeypatch.setattr(GeneratorUtil, "create_generator", lambda *args, **kwargs: generator)

    assert task._generate_value(SimpleNamespace()) is value
    assert generator.calls == 1
    assert task._generator is generator
    assert task._mode == KeyTask._GENERATOR_MODE


@pytest.mark.parametrize("mode", [KeyTask._GENERATOR_MODE, KeyTask._LAZY_GENERATOR_MODE])
def test_native_generator_value_path_keeps_exception_identity_and_one_call(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    error = RuntimeError("native failure")
    generator = NativeGenerator(None, error)
    task = _task(generator, mode)
    monkeypatch.setattr(GeneratorUtil, "create_generator", lambda *args, **kwargs: generator)

    with pytest.raises(RuntimeError) as caught:
        task._generate_value(SimpleNamespace())

    assert caught.value is error
    assert error.args == ("native failure",)
    assert error.__cause__ is None
    assert error.__context__ is None
    assert generator.calls == 1


def test_generator_branch_keeps_numpy_boolean_normalization() -> None:
    generator = NativeGenerator(numpy.bool_(True))

    assert _task(generator, KeyTask._GENERATOR_MODE)._generate_value(SimpleNamespace()) is True
    assert generator.calls == 1


def test_literal_base_keeps_abc_body_rng_and_cache_policy() -> None:
    with pytest.raises(TypeError, match="abstract"):
        BaseLiteralGenerator()
    generator = NativeGenerator(object())
    original_rng = generator.rng
    assert isinstance(original_rng, Random)
    replacement_rng = Random(19)
    generator.rng = replacement_rng
    assert generator.rng is replacement_rng
    assert generator.cache_in_root is True
    with pytest.raises(NotImplementedError) as caught:
        BaseLiteralGenerator.generate(generator)
    assert caught.value.args == ("Subclasses must implement this method",)
    assert generator.calls == 0


def test_literal_base_declares_native_object_without_widening_specialized_return() -> None:
    assert get_type_hints(BaseLiteralGenerator.generate) == {"return": object}
    assert get_type_hints(StringGenerator.generate)["return"] is str
    assert get_type_hints(DataFakerGenerator.generate)["return"] is object
