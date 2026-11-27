# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.io.api import RegisteredClient
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager


def _context(
    clients: dict[str, RegisteredClient] | None = None,
    namespace: dict[str, object] | None = None,
    global_variables: dict[str, object] | None = None,
    properties: dict[str, object] | None = None,
) -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="context-test",
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
        clients=clients,
        properties=properties,
        namespace={"nested": [1]} if namespace is None else namespace,
        global_variables={"shared": [1]} if global_variables is None else global_variables,
        generators={"cached": [1]},
        run_seed=RunSeed.create(7),
    )
