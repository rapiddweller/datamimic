# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Integration tests for root-level generator caching behaviour."""

from pathlib import Path

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.common.literal_generators.generator_util import GeneratorUtil
from datamimic_ce.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.model.generator_model import GeneratorModel
from datamimic_ce.product_storage.memstore_manager import MemstoreManager
from datamimic_ce.statements.generator_statement import GeneratorStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.tasks.generator_task import GeneratorTask


class DummyStatement(Statement):
    """Minimal statement used for generator creation in tests."""

    def __init__(self, name: str = "dummy"):
        super().__init__(name, None)


class CachedGenerator(BaseLiteralGenerator):
    def generate(self):  # pragma: no cover - trivial
        return "cached"


class NonCachedGenerator(BaseLiteralGenerator):
    cache_in_root = False

    def generate(self):  # pragma: no cover - trivial
        return "non_cached"


def _create_context() -> SetupContext:
    """Create a minimal setup context for testing."""

    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="t",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator=",",
        default_locale="en_US",
        default_dataset="default",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=None,
        default_variable_prefix="${",
        default_variable_suffix="}",
        default_line_separator="\n",
    )


def test_root_caching_behaviour():
    ctx = _create_context()
    ctx.namespace.update({
        "CachedGenerator": CachedGenerator,
        "NonCachedGenerator": NonCachedGenerator,
    })

    util = GeneratorUtil(ctx)
    stmt = DummyStatement()

    # Generators with default caching should be reused
    gen1 = util.create_generator("CachedGenerator()", stmt)
    gen2 = util.create_generator("CachedGenerator()", stmt)
    assert gen1 is gen2

    # Generators opting out of caching should create new instances
    gen3 = util.create_generator("NonCachedGenerator()", stmt)
    gen4 = util.create_generator("NonCachedGenerator()", stmt)
    assert gen3 is not gen4
    assert "NonCachedGenerator()" not in ctx.root.generators

    # GeneratorTask should honour cache_in_root when registering generators
    stmt_cached = GeneratorStatement(GeneratorModel(name="cached", generator="CachedGenerator()"))
    GeneratorTask(stmt_cached).execute(ctx)
    assert "cached" in ctx.root.generators

    stmt_non_cached = GeneratorStatement(GeneratorModel(name="non_cached", generator="NonCachedGenerator()"))
    GeneratorTask(stmt_non_cached).execute(ctx)
    assert "non_cached" not in ctx.root.generators
