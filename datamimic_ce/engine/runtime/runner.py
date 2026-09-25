"""Runtime descriptor execution lifecycle."""

from __future__ import annotations

import logging
import os
import uuid

# Must be set before importing Ray through runtime tasks.
os.environ["RAY_DEDUP_LOGS"] = "0"

from datamimic_ce.engine.dsl.api import DescriptorParser, GenerateStatement, SetupStatement
from datamimic_ce.engine.io.api import TestResultExporter
from datamimic_ce.engine.runtime.config import settings
from datamimic_ce.engine.runtime.contracts import CapturedProducts, FactoryConfig, RunRequest, RunResult
from datamimic_ce.engine.runtime.logging import log_memory_info, log_system_info, setup_logger
from datamimic_ce.engine.runtime.process import bootstrap_process_title, set_main_process_title
from datamimic_ce.engine.runtime.tasks.setup_task import SetupTask

logger = logging.getLogger("DATAMIMIC")


class RuntimeRunSession:
    def __init__(self, request: RunRequest):
        self._task_id = request.task_id or uuid.uuid4().hex
        bootstrap_process_title()
        set_main_process_title(self._task_id, request.descriptor_path.name)

        if request.args is None:
            log_level = logging.INFO
        else:
            try:
                configured_level = logging.getLevelName(request.args.log_level.upper())
            except AttributeError:
                configured_level = logging.INFO
            log_level = configured_level if isinstance(configured_level, int) else logging.INFO
        setup_logger(logger_name="DATAMIMIC", worker_name="MAIN", level=log_level)

        self._request = request
        self._test_result_storage = TestResultExporter()

        log_system_info()
        log_memory_info(request.platform_configs.root if request.platform_configs is not None else None)
        logger.info(f"Task ID: {self._task_id}")

        if not request.descriptor_path.is_file():
            logger.error(f"Invalid descriptor file path: {request.descriptor_path}")
            raise ValueError(f"Invalid file path: {request.descriptor_path}")

    @staticmethod
    def _get_stmt_by_entity_name(stmt: object, factory_config: FactoryConfig) -> GenerateStatement | None:
        if not isinstance(stmt, GenerateStatement):
            return None
        if stmt.name == factory_config.entity_name:
            return stmt
        for sub_stmt in stmt.sub_statements:
            result = RuntimeRunSession._get_stmt_by_entity_name(sub_stmt, factory_config)
            if result is not None:
                return result
        return None

    def _validate_xml_model(self, root_stmt: SetupStatement, factory_config: FactoryConfig) -> None:
        if root_stmt.num_process is not None and root_stmt.num_process > 1:
            logger.warning("Multiple processes are not supported in factory mode")

        entity_stmt = None
        for stmt in root_stmt.sub_statements:
            entity_stmt = self._get_stmt_by_entity_name(stmt, factory_config)
            if entity_stmt is not None:
                break

        if entity_stmt is None:
            logger.error(f"Entity name '{factory_config.entity_name}' not found in the XML model")
            raise ValueError(f"Entity name '{factory_config.entity_name}' not found in the XML model")

        if entity_stmt.count is not None:
            logger.warning("Count is not supported in factory mode")
            entity_stmt.count = str(factory_config.count)

        if len(entity_stmt.targets) > 1:
            logger.warning("Targets are not supported in factory mode")
            entity_stmt.targets = set()

    def execute(self) -> RunResult:
        request = self._request
        try:
            properties = request.platform_props.root if request.platform_props is not None else None
            root_stmt = DescriptorParser.parse(request.descriptor_path, properties, settings.RUNTIME_ENVIRONMENT)
            if request.factory_config is not None:
                self._validate_xml_model(root_stmt, request.factory_config)
            if request.statement_transformer is not None:
                request.statement_transformer(root_stmt)

            SetupTask(
                setup_stmt=root_stmt,
                memstore_manager=None,
                task_id=self._task_id,
                properties=properties,
                test_mode=request.test_mode,
                test_result_storage=self._test_result_storage,
                descriptor_dir=request.descriptor_path.parent,
                runtime_environment=settings.RUNTIME_ENVIRONMENT,
                ray_debug=settings.RAY_DEBUG,
            ).execute()
        except ValueError as error:
            logger.error(f"Value error: {error}")
            raise error
        except Exception as error:
            logger.exception(f"Error in DATAMIMIC process. Error message: {error}")
            raise error
        captured = (
            CapturedProducts.model_construct(root=self._test_result_storage.get_result()) if request.test_mode else None
        )
        return RunResult(captured)

    def capture_test_result(self) -> CapturedProducts | None:
        if self._request.test_mode:
            return CapturedProducts.model_construct(root=self._test_result_storage.get_result())
        raise ValueError("Cannot capture test result in non-test mode") from None


def create_run_session(request: RunRequest) -> RuntimeRunSession:
    return RuntimeRunSession(request)


def run(request: RunRequest) -> RunResult:
    return create_run_session(request).execute()
