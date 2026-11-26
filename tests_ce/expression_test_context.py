# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Shared isolated context for expression tests."""

from pathlib import Path

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager


def expression_context(*, namespace: dict[str, object] | None = None, seeded: bool = False) -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="expression-evaluation-test",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator="\n",
        namespace=namespace,
        run_seed=RunSeed.create(7 if seeded else None),
    )
