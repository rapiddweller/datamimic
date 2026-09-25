# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import argparse
import uuid
from pathlib import Path

from datamimic_ce.interfaces.api import create_run_session
from datamimic_ce.interfaces.contracts import (
    FactoryConfig,
    PlatformConfiguration,
    PlatformProperties,
    RunRequest,
    RunSession,
    StatementTransformer,
)


class DataMimic:
    def __init__(
        self,
        descriptor_path: Path,
        task_id: str | None = None,
        platform_props: dict[str, str] | None = None,
        platform_configs: dict | None = None,
        test_mode: bool = False,
        factory_config: FactoryConfig | None = None,
        args: argparse.Namespace | None = None,
        statement_transformer: StatementTransformer | None = None,
    ):
        """Initialize a runtime session for the descriptor."""
        self._task_id = task_id or uuid.uuid4().hex
        self._session: RunSession = create_run_session(
            RunRequest(
                descriptor_path=descriptor_path,
                task_id=self._task_id,
                platform_props=PlatformProperties.model_construct(root=platform_props)
                if platform_props is not None
                else None,
                platform_configs=PlatformConfiguration.model_construct(root=platform_configs)
                if platform_configs is not None
                else None,
                test_mode=test_mode,
                factory_config=factory_config,
                args=args,
                statement_transformer=statement_transformer,
            )
        )

    def parse_and_execute(self) -> None:
        """Parse the descriptor and execute its setup task."""
        self._session.execute()

    def capture_test_result(self) -> dict | None:
        """Capture test result in test mode."""
        captured = self._session.capture_test_result()
        return captured.root if captured is not None else None
