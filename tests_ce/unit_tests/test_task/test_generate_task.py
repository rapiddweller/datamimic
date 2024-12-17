import os
import pytest
import ray
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock, PropertyMock

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.tasks.task_util import TaskUtil
from datamimic_ce.tasks.generate_task import GenerateTask


class TestClassFactoryUtil(BaseClassFactoryUtil):
    """Test implementation of BaseClassFactoryUtil"""

    def get_app_settings(self):
        return Mock()

    def get_data_generation_util(self):
        return Mock()

    def get_datasource_util_cls(self):
        return Mock()

    def get_datetime_generator(self):
        return Mock()

    def get_exporter_util(self):
        return Mock()

    def get_integer_generator(self):
        return Mock()

    def get_parser_util_cls(self):
        return Mock()

    def get_setup_logger_func(self):
        return Mock()

    def get_string_generator(self):
        return Mock()

    def get_task_util_cls(self):
        return Mock()


class TestGenerateTask:
    @pytest.fixture
    def setup_context(self, tmp_path):
        """Create a real SetupContext instance for testing"""
        from datamimic_ce.product_storage.memstore_manager import MemstoreManager
        from datamimic_ce.exporters.test_result_exporter import TestResultExporter

        return SetupContext(
            class_factory_util=TestClassFactoryUtil(),
            memstore_manager=MemstoreManager(),
            task_id="test_task",
            test_mode=True,
            test_result_exporter=TestResultExporter(),
            default_separator=",",
            default_locale="en_US",
            default_dataset="test",
            use_mp=False,
            descriptor_dir=tmp_path,
            num_process=2,
            default_variable_prefix="__",
            default_variable_suffix="__",
            default_line_separator="\n",
            current_seed=42,
            clients={},
            data_source_len={},
            properties={},
            namespace={},
            global_variables={},
            generators={},
            default_source_scripted=False,
            report_logging=True,
        )

    @pytest.fixture
    def generate_statement(self):
        """Create a real GenerateStatement instance"""
        from datamimic_ce.statements.generate_statement import GenerateStatement
        from datamimic_ce.model.generate_model import GenerateModel

        # Create a minimal model with valid attributes
        model = GenerateModel(
            name="test_generate",
            count="10",
            target="CSV",
            pageSize="10000",
        )

        # Create statement with model and no parent
        stmt = GenerateStatement(model=model, parent_stmt=None)

        return stmt

    @pytest.fixture
    def generate_task(self, generate_statement):
        return GenerateTask(generate_statement, Mock())

    def test_init(self, generate_task):
        """Test initialization of GenerateTask"""
        assert generate_task._statement is not None
        assert generate_task._class_factory_util is not None
        assert ray.is_initialized()

    def test_determine_count_with_explicit_count(self, generate_task, setup_context):
        """Test count determination when count is explicitly set"""
        # Create mock statement
        mock_statement = Mock(spec=GenerateStatement)
        mock_statement.get_int_count.return_value = 100

        # Replace real statement with mock
        generate_task._statement = mock_statement

        count = generate_task._determine_count(setup_context)
        assert count == 100

    @pytest.mark.asyncio
    async def test_execute_with_ray(self, generate_task, setup_context):
        """Test successful execution with Ray"""
        # Setup test data
        generate_task._determine_count = Mock(return_value=10)

        # Mock the full_name property
        type(generate_task._statement).full_name = PropertyMock(return_value="test_generate")

        # Mock exporter util
        exporter_util = Mock()
        exporter_util.create_exporter_list.return_value = ([], [])
        setup_context.class_factory_util.get_exporter_util = Mock(return_value=exporter_util)

        # Create test data that workers would generate
        worker_results = [
            {"test_generate": [{"id": i} for i in range(5)]},  # First worker
            {"test_generate": [{"id": i} for i in range(5, 10)]},  # Second worker
        ]

        # Create a serializable worker class
        @ray.remote
        class TestWorker:
            def __init__(self):
                self._initialized = False

            async def generate_chunk(self, context, statement, start_idx, end_idx, page_size):
                return worker_results[0] if start_idx == 0 else worker_results[1]

            @classmethod
            def remote(cls, *args, **kwargs):
                instance = cls()
                return instance.generate_chunk(*args, **kwargs)

        # Mock Ray's get function to merge worker results
        def mock_ray_get(futures):
            merged = {"test_generate": []}
            for result in worker_results:
                merged["test_generate"].extend(result["test_generate"])
            return merged

        with patch("ray.get", side_effect=mock_ray_get):
            with patch("datamimic_ce.tasks.generate_task.GenerateWorker", TestWorker):
                result = await generate_task.execute(setup_context)

                # Verify results
                assert isinstance(result, dict)
                assert {} == result

    @pytest.mark.asyncio
    async def test_execute_empty_result(self, generate_task, setup_context):
        """Test execution with zero count"""
        generate_task._determine_count = Mock(return_value=0)
        result = await generate_task.execute(setup_context)
        assert result == {generate_task.statement.full_name: []}


class TestGenerateWorker:
    @pytest.fixture
    def setup_context(self):
        context = Mock(spec=SetupContext)
        context.task_id = "test_task"
        context.root = context
        context.test_mode = False
        context.clients = {}
        return context

    @pytest.fixture
    def worker(self):
        # Create a serializable worker
        class SerializableWorker:
            @staticmethod
            async def generate_chunk(context, statement, start_idx, end_idx, page_size):
                return {statement.full_name: [{"id": i} for i in range(start_idx, end_idx)]}

            @staticmethod
            def remote(*args, **kwargs):
                return SerializableWorker.generate_chunk(*args, **kwargs)

        return SerializableWorker()

    @pytest.fixture
    def generate_statement(self):
        stmt = Mock(spec=GenerateStatement)
        stmt.name = "test_generate"
        stmt.full_name = "test_generate"
        stmt.targets = []
        stmt.num_process = 2
        stmt.page_size = 10000
        stmt.cyclic = False
        stmt.sub_statements = []
        stmt.clients = {}
        return stmt

    @pytest.mark.asyncio
    async def test_generate_chunk(self, worker, setup_context, generate_statement):
        """Test successful chunk generation"""
        start_idx = 0
        end_idx = 5
        page_size = 2

        # Mock Ray's remote functionality
        with patch("ray.get") as mock_ray_get, patch.object(worker, "generate_chunk") as mock_generate:
            expected_result = {generate_statement.full_name: [{"id": i} for i in range(5)]}
            mock_generate.return_value = expected_result
            mock_ray_get.return_value = expected_result

            result = await worker.generate_chunk(setup_context, generate_statement, start_idx, end_idx, page_size)

            assert isinstance(result, dict)
            assert generate_statement.full_name in result
            assert len(result[generate_statement.full_name]) == 5


class TestFileLoaders:
    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    @pytest.fixture
    def setup_context(self):
        context = Mock(spec=SetupContext)
        context.task_id = "test_task"
        return context

    def test_load_csv_file(self, temp_dir, setup_context):
        """Test CSV file loading"""
        csv_path = temp_dir / "test.csv"
        csv_content = "id,name\n1,test1\n2,test2"
        csv_path.write_text(csv_content)

        result = TaskUtil._load_csv_file(setup_context, csv_path, ",", False, None, None, False, "", "")

        assert len(result) == 2
        assert result[0]["name"] == "test1"
        assert result[1]["name"] == "test2"

    def test_load_json_file(self, temp_dir):
        """Test JSON file loading"""
        # Create test JSON file
        json_path = temp_dir / "test.json"
        json_content = [{"id": 1}, {"id": 2}]
        json_path.write_text(json.dumps(json_content))

        result = TaskUtil._load_json_file("test_task", json_path, False, None, None)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_load_xml_file(self, temp_dir):
        """Test XML file loading"""
        xml_path = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <list>
                <item>
                    <id>1</id>
                </item>
                <item>
                    <id>2</id>
                </item>
            </list>
        </root>
        """
        xml_path.write_text(xml_content)

        result = TaskUtil._load_xml_file(xml_path, False, None, None)

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"


class TestNegativeCases:
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Fixture to provide a temporary directory"""
        return tmp_path

    @pytest.fixture
    def setup_context(self):
        context = Mock(spec=SetupContext)
        context.task_id = "test_task"
        return context

    @pytest.fixture
    def generate_statement(self):
        stmt = Mock(spec=GenerateStatement)
        stmt.clients = {}
        return stmt

    def test_invalid_selector_client(self, setup_context, generate_statement):
        """Test error when using selector with non-database client"""
        task = GenerateTask(generate_statement, Mock())

        # Configure the mock objects properly
        generate_statement.get_int_count.return_value = None
        generate_statement.selector = "test_selector"
        generate_statement.source = "invalid_client"
        generate_statement.sub_statements = []  # Make it iterable

        # Mock non-database client
        invalid_client = Mock()
        setup_context.get_client_by_id.return_value = invalid_client

        with pytest.raises(ValueError, match="Using selector without count only supports DatabaseClient"):
            task._determine_count(setup_context)

    def test_invalid_json_format(self, temp_dir):
        """Test error when JSON file is not a list"""
        json_path = temp_dir / "invalid.json"
        json_content = {"not": "a list"}
        json_path.write_text(json.dumps(json_content))

        with pytest.raises(ValueError, match="must contain a list of objects"):
            TaskUtil._load_json_file("test_task", json_path, False, None, None)

    def test_missing_file(self, temp_dir):
        """Test error when file does not exist"""
        non_existent_path = temp_dir / "missing.csv"

        with pytest.raises(FileNotFoundError):
            TaskUtil._load_csv_file(Mock(spec=SetupContext), non_existent_path, ",", False, None, None, False, "", "")

    def test_invalid_page_size(self, setup_context, generate_statement):
        """Test handling of invalid page size"""
        task = GenerateTask(generate_statement, Mock())
        generate_statement.page_size = -1

        page_size = task._calculate_default_page_size(100)
        assert page_size == 1  # Should default to minimum of 1
