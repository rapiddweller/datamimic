# test_generate_task.py

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.product_storage.memstore_manager import MemstoreManager
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.tasks.generate_task import GenerateTask
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.dict_util import dict_nested_update


class TestGenerateTask:
    @pytest.fixture
    def mock_gen_iter_context(self) -> GenIterContext:
        """Setup a comprehensive mock of GenIterContext with all required attributes and methods."""
        # Create the mock for GenIterContext
        gen_iter_context = MagicMock(spec=GenIterContext)

        # Set up attributes with realistic values
        gen_iter_context._current_name = "test_name"
        gen_iter_context._current_product = {"field1": "value1"}
        gen_iter_context._current_variables = {"var1": "value1"}
        gen_iter_context._namespace = {"CustomClass": MagicMock()}

        # Mock the parent context
        gen_iter_context._parent = MagicMock(spec=SetupContext)
        type(gen_iter_context).parent = PropertyMock(return_value=gen_iter_context._parent)

        # Property methods
        type(gen_iter_context).current_name = PropertyMock(return_value=gen_iter_context._current_name)
        type(gen_iter_context).current_product = PropertyMock(
            return_value=gen_iter_context._current_product,
            fset=lambda self, value: setattr(self, "_current_product", value),
        )
        type(gen_iter_context).current_variables = PropertyMock(return_value=gen_iter_context._current_variables)

        # Mock methods
        gen_iter_context.get_namespace.return_value = gen_iter_context._namespace

        def mock_add_current_product_field(key_path, value):
            """Mock method to update current product using a key path."""
            dict_nested_update(gen_iter_context._current_product, key_path, value)

        gen_iter_context.add_current_product_field.side_effect = mock_add_current_product_field

        return gen_iter_context

    @pytest.fixture
    def mock_context(self) -> SetupContext:
        """Setup a comprehensive mock of SetupContext with all required attributes and methods."""
        # Create the context mock
        context = MagicMock(spec=SetupContext)
        context.root = context  # For nested context access

        # Set attributes with realistic values
        context.use_mp = True
        context.test_mode = False
        context.report_logging = True
        context.num_process = 4
        context.task_id = "test_task_id"
        context.descriptor_dir = Path("/path/to/descriptors")
        context.data_source_len = {"test_full_name": 1000}
        context.default_variable_prefix = "{{"
        context.default_variable_suffix = "}}"
        context.default_separator = ","
        context.default_locale = "en_US"
        context.default_dataset = "default"
        context.default_source_scripted = False
        context.default_line_separator = "\n"
        context.default_encoding = "utf-8"
        context.global_variables = {"var1": "value1"}
        context.generators = {"gen1": MagicMock()}
        context.properties = {"prop1": "value1"}
        context.namespace = {"CustomClass": MagicMock()}
        context.current_seed = 42

        # Setup class factory utility
        context.class_factory_util = MagicMock(spec=BaseClassFactoryUtil)
        datasource_util = MagicMock()
        context.class_factory_util.get_datasource_registry.return_value = datasource_util

        # Setup exporter utility
        exporter_util = MagicMock()
        exporter_util.create_exporter_list.return_value = ([], [])
        context.class_factory_util.get_exporter_util.return_value = exporter_util

        # Setup memstore manager
        context.memstore_manager = MagicMock(spec=MemstoreManager)
        context.memstore_manager.contain.return_value = False

        # Setup clients
        mock_mongo_client = MagicMock(spec=MongoDBClient)
        context.clients = {"mongodb": mock_mongo_client}

        # Mock methods
        context.get_client_by_id.return_value = mock_mongo_client
        context.add_client = MagicMock()

        # Mock for evaluating namespace
        def mock_eval_namespace(content):
            updated_fields = {"dynamic_var": "new_value"}
            context.namespace.update(updated_fields)
            return updated_fields

        context.eval_namespace.side_effect = mock_eval_namespace

        return context

    @pytest.fixture
    def mock_statement(self):
        """Setup statement mock with all required attributes and methods."""
        statement = MagicMock(spec=GenerateStatement)

        # Set basic attributes
        statement.full_name = "test_full_name"
        statement.name = "test_name"
        statement.sub_statements = []
        statement.targets = {"mongodb.upsert", "file.write"}
        statement.selector = "test_selector"
        statement.source = "test_source"
        statement.multiprocessing = True
        statement.page_size = 10000
        statement.cyclic = True
        statement.bucket = "test_bucket"
        statement.container = "test_container"
        statement.variable_prefix = "test_prefix"
        statement.variable_suffix = "test_suffix"
        statement.distribution = "uniform"
        statement.converter = "json"
        statement._count = 1000
        statement._source_uri = "mongodb://localhost:27017"
        statement._separator = ","
        statement._storage_id = "custom-storage-id"
        statement.export_uri = "s3://export-bucket"

        # Configure methods
        statement.get_int_count.return_value = statement._count
        statement.contain_mongodb_upsert.return_value = True
        statement.retrieve_sub_statement_by_fullname.return_value = None

        # Configure methods
        statement.get_int_count.return_value = statement._count
        statement.contain_mongodb_upsert.return_value = True

        # Adjust the sub-statement retrieval
        def mock_retrieve_sub_statement_by_fullname(name):
            if name == statement.full_name:
                return statement
            return None

        statement.retrieve_sub_statement_by_fullname.side_effect = mock_retrieve_sub_statement_by_fullname

        return statement

    @pytest.fixture
    def generate_task(self, mock_statement):
        """Create GenerateTask instance with mocked dependencies."""
        class_factory_util = MagicMock(spec=BaseClassFactoryUtil)
        return GenerateTask(mock_statement, class_factory_util)

    def test_determine_count_default(self, generate_task, mock_context):
        """Test _determine_count when no count is specified."""
        mock_context.data_source_len = {generate_task.statement.full_name: 1000}
        count = generate_task._determine_count(mock_context)
        assert count == 1000

    def test_determine_count_with_explicit_count(self, generate_task, mock_context, mock_statement):
        """Test _determine_count with an explicitly set count."""
        mock_statement.get_int_count.return_value = 500
        count = generate_task._determine_count(mock_context)
        assert count == 500
        mock_statement.get_int_count.assert_called_once_with(mock_context)

    def test_determine_count_with_selector(self, generate_task, mock_context, mock_statement):
        """Test count determination using a selector."""
        mock_statement.get_int_count.return_value = None  # Add this line
        mock_statement.selector = "test_selector"
        mock_statement.source = "test_source"
        mock_client = MagicMock(spec=DatabaseClient)
        mock_client.count_query_length.return_value = 750
        mock_context.root.get_client_by_id.return_value = mock_client

        count = generate_task._determine_count(mock_context)

        assert count == 750
        mock_client.count_query_length.assert_called_once_with("test_selector")

    def test_determine_count_with_selector_invalid_client(self, generate_task, mock_context, mock_statement):
        """Test error when using selector with a non-database client."""
        mock_statement.get_int_count.return_value = None  # Add this line
        mock_statement.selector = "test_selector"
        mock_statement.source = "test_source"
        mock_context.root.get_client_by_id.return_value = MagicMock()

        with pytest.raises(ValueError, match=".*only supports DatabaseClient.*"):
            generate_task._determine_count(mock_context)

    def test_calculate_default_page_size(self, generate_task, mock_statement):
        """Test _calculate_default_page_size calculation."""
        # Test with entity count > 10000
        size = generate_task._calculate_default_page_size(15000)
        assert size == 10000

        # Test with statement page_size set
        mock_statement.page_size = 500
        size = generate_task._calculate_default_page_size(15000)
        assert size == 500

    @pytest.mark.parametrize(
        "entity_count, expected_size",
        [
            (0, 1),
            (50, 50),
            (500, 500),
            (5000, 5000),
            (15000, 10000),  # Max default page size is 10,000
        ],
    )
    def test_calculate_default_page_size_various_counts(
            self, generate_task, mock_statement, entity_count, expected_size
    ):
        """Test _calculate_default_page_size with various entity counts."""
        mock_statement.page_size = None
        size = generate_task._calculate_default_page_size(entity_count)
        assert size == expected_size

    def test_calculate_default_page_size_with_statement_page_size(self, generate_task, mock_statement):
        """Test page size when the statement's page_size is set."""
        mock_statement.page_size = 100
        size = generate_task._calculate_default_page_size(1000)
        assert size == 100
        assert mock_statement.page_size == 100

    @pytest.mark.skip("Need rework with ray")
    def test_execute_single_process(self, generate_task, mock_context, mock_statement):
        """Test single-process execution flow."""
        with (
            patch.object(generate_task, "_sp_generate") as mock_sp_generate,
            patch.object(generate_task, "_calculate_default_page_size") as mock_calc_page_size,
        ):
            mock_sp_generate.return_value = {"test_full_name": []}
            mock_calc_page_size.return_value = 100

            # Execute with multiprocessing disabled
            mock_context.use_mp = False
            mock_context.num_process = 1  # Add this line
            mock_statement.multiprocessing = False  # Ensure multiprocessing is disabled
            mock_statement.get_int_count.return_value = 1000

            generate_task.execute(mock_context)

            mock_sp_generate.assert_called()
            mock_calc_page_size.assert_called()

    @pytest.mark.skip("Need rework with ray")
    def test_execute_multiprocess(self, generate_task, mock_context, mock_statement):
        """Test multiprocess execution flow."""
        with (
            patch.object(generate_task, "_mp_page_process") as mock_mp_process,
            patch.object(generate_task, "_calculate_default_page_size") as mock_calc_page_size,
        ):
            # Enable multiprocessing
            mock_statement.multiprocessing = True
            mock_context.use_mp = True
            mock_statement.get_int_count.return_value = 1000
            mock_calc_page_size.return_value = 100

            generate_task.execute(mock_context)

            mock_mp_process.assert_called_once()
            mock_calc_page_size.assert_called_once()

    def test_scan_data_source(self, generate_task, mock_context):
        """Test _scan_data_source method."""
        datasource_util = mock_context.class_factory_util.get_datasource_registry.return_value

        GenerateTask._scan_data_source(mock_context, generate_task.statement)

        datasource_util.set_data_source_length.assert_called_once_with(mock_context, generate_task.statement)

    @staticmethod
    def _get_chunk_indices(chunk_size: int, data_count: int) -> list:
        """
        Create list of chunk indices based on chunk size and required data count.

        :param chunk_size: Size of each chunk.
        :param data_count: Total data count.
        :return: List of tuples representing chunk indices.
        """
        return [(i, min(i + chunk_size, data_count)) for i in range(0, data_count, chunk_size)]

    def test_get_chunk_indices(self, generate_task):
        """Test _get_chunk_indices calculation."""
        indices = TestGenerateTask._get_chunk_indices(100, 250)
        expected = [(0, 100), (100, 200), (200, 250)]
        assert indices == expected

    def test_pre_execute(self, generate_task, mock_context, mock_statement):
        """Test pre_execute method."""
        # Setup
        key_statement = MagicMock(spec=KeyStatement)
        mock_statement.sub_statements = [key_statement]

        # Mock task util and task
        task_util = MagicMock()
        mock_task = MagicMock()
        task_util.get_task_by_statement.return_value = mock_task
        mock_context.class_factory_util.get_task_util_cls.return_value = task_util

        # Execute
        generate_task.pre_execute(mock_context)

        # Verify
        task_util.get_task_by_statement.assert_called_once_with(mock_context.root, key_statement, None)
        mock_task.pre_execute.assert_called_once_with(mock_context)

    @pytest.mark.skip("Need rework with ray")
    @pytest.mark.parametrize(
        "multiprocessing,use_mp,has_mongodb_delete,expected_use_mp",
        [
            (True, False, False, True),  # Explicit multiprocessing
            (None, True, False, True),  # Default to context setting
            (None, True, True, False),  # MongoDB delete prevents MP
            (False, False, False, False),  # Explicitly disabled
        ],
    )
    def test_multiprocessing_decision(self, mock_context, multiprocessing, use_mp, has_mongodb_delete, expected_use_mp):
        """Test multiprocessing decision logic with proper mock objects."""
        # Create a mock GenerateStatement with spec
        mock_statement = MagicMock(spec=GenerateStatement)
        mock_statement.multiprocessing = multiprocessing
        mock_statement.get_int_count.return_value = 100

        # Create a mock SetupContext with spec
        mock_context.use_mp = use_mp

        # Mock exporter util
        exporter_util = MagicMock()
        mock_context.class_factory_util.get_exporter_util.return_value = exporter_util

        if has_mongodb_delete:
            # Create a mock MongoDBExporter with spec
            mock_mongo_exporter = MagicMock(spec=MongoDBExporter)
            exporter_util.create_exporter_list.return_value = ([(mock_mongo_exporter, "delete")], [])
        else:
            exporter_util.create_exporter_list.return_value = ([], [])

        # Create the GenerateTask with the mock_statement and class_factory_util
        generate_task = GenerateTask(mock_statement, mock_context.class_factory_util)

        # Mock methods
        with (
            patch.object(generate_task, "_mp_page_process") as mock_mp_process,
            patch.object(generate_task, "_sp_generate") as mock_sp_generate,
            patch.object(generate_task, "_calculate_default_page_size", return_value=100),
        ):
            generate_task.execute(mock_context)

            if expected_use_mp:
                mock_mp_process.assert_called_once()
                mock_sp_generate.assert_not_called()
            else:
                mock_mp_process.assert_not_called()
                mock_sp_generate.assert_called_once()

    @pytest.mark.skip("Need rework with ray")
    def test_sp_generate(self, generate_task, mock_context, mock_statement):
        """Test _sp_generate method."""
        with patch("datamimic_ce.tasks.generate_task._geniter_single_process_generate") as mock_gen:
            mock_gen.return_value = {mock_statement.full_name: [{"field1": "value1"}]}
            result = generate_task._sp_generate(mock_context, 0, 10)
            assert result == {mock_statement.full_name: [{"field1": "value1"}]}
            mock_gen.assert_called_once()

    @pytest.mark.skip("Need rework with ray")
    def test_prepare_mp_generate_args(self, generate_task, mock_context):
        """Test _prepare_mp_generate_args method."""
        setup_ctx = mock_context
        single_process_execute_function = MagicMock()
        count = 1000
        num_processes = 4
        page_size = 100

        with patch("dill.dumps") as mock_dill_dumps:
            mock_dill_dumps.return_value = b"serialized_data"
            args_list = generate_task._prepare_mp_generate_args(
                setup_ctx,
                single_process_execute_function,
                count,
                num_processes,
                page_size,
            )
            assert len(args_list) == num_processes
            for args in args_list:
                assert len(args) == 8  # Number of arguments
                assert args[0] == setup_ctx
                assert args[1] == generate_task.statement
                assert isinstance(args[2], tuple)  # chunk_data
                assert args[3] == single_process_execute_function
                assert args[4] == b"serialized_data"  # namespace_functions
                assert isinstance(args[5], int)  # mp_idx
                assert args[6] == page_size
                assert isinstance(args[7], int)  # mp_chunk_size

    @pytest.mark.skip("Need rework with ray")
    def test_mp_page_process(self, generate_task, mock_context):
        """Test _mp_page_process method."""
        with (
            patch("multiprocessing.Pool") as mock_pool_class,
            patch.object(generate_task, "_prepare_mp_generate_args") as mock_prepare_args,
        ):
            mock_pool = mock_pool_class.return_value.__enter__.return_value
            # Mock args_list with tuples that have 8 elements
            mock_prepare_args.return_value = [
                (mock_context, generate_task.statement, (0, 100), MagicMock(), b"serialized_data", 1, 100, 250),
                (mock_context, generate_task.statement, (100, 200), MagicMock(), b"serialized_data", 2, 100, 250),
            ]
            mock_context.test_mode = False
            mock_context.memstore_manager.contain.return_value = False

            generate_task._mp_page_process(mock_context, 100, MagicMock())

            mock_pool.map.assert_called_once()
            mock_prepare_args.assert_called_once()

    @pytest.mark.skip("Need rework with ray")
    def test_execute_include(self):
        """Test execute_include static method with proper mock objects."""
        # Setup
        # Create a SetupStatement with an empty list of sub_statements
        setup_stmt = MagicMock(spec=SetupStatement)
        setup_stmt.sub_statements = []

        # Create a root context, which is a SetupContext
        root_context = MagicMock(spec=SetupContext)
        root_context.global_variables = {}
        root_context.class_factory_util = MagicMock(spec=BaseClassFactoryUtil)

        # Create a parent context, which is a GenIterContext
        parent_context = MagicMock(spec=GenIterContext)
        parent_context.root = root_context
        parent_context.current_variables = {"var1": "value1"}
        parent_context.current_product = {"prod1": "value1"}

        # Mock the deepcopy to return a new mock of root_context
        copied_root_context = MagicMock(spec=SetupContext)
        copied_root_context.global_variables = {}
        copied_root_context.class_factory_util = root_context.class_factory_util

        with patch("copy.deepcopy", return_value=copied_root_context):
            # Execute
            GenerateTask.execute_include(setup_stmt, parent_context)

        # Verify that update_with_stmt was called on the copied_root_context
        copied_root_context.update_with_stmt.assert_called_once_with(setup_stmt)

        # Verify that get_task_util_cls was called
        copied_root_context.class_factory_util.get_task_util_cls.assert_called_once()
        # Since there are no sub_statements, get_task_by_statement should not be called
        task_util_cls = copied_root_context.class_factory_util.get_task_util_cls.return_value
        task_util_cls.get_task_by_statement.assert_not_called()

        # Now, test with sub_statements
        # Add a sub_statement to setup_stmt
        stmt = MagicMock()
        setup_stmt.sub_statements = [stmt]
        mock_task = MagicMock()
        task_util_cls.get_task_by_statement.return_value = mock_task

        with patch("copy.deepcopy", return_value=copied_root_context):
            # Execute again
            GenerateTask.execute_include(setup_stmt, parent_context)

        # Verify that get_task_by_statement was called with the correct arguments
        task_util_cls.get_task_by_statement.assert_called_with(copied_root_context, stmt)
        # Verify that task.execute was called with the copied_root_context
        mock_task.execute.assert_called_with(copied_root_context)

    @pytest.mark.parametrize(
        "chunk_size,data_count,expected",
        [
            (100, 0, []),
            (100, 50, [(0, 50)]),
            (100, 100, [(0, 100)]),
            (100, 150, [(0, 100), (100, 150)]),
            (100, 250, [(0, 100), (100, 200), (200, 250)]),
        ],
    )
    def test_get_chunk_indices_various(self, generate_task, chunk_size, data_count, expected):
        """Test _get_chunk_indices with various inputs."""
        indices = TestGenerateTask._get_chunk_indices(chunk_size, data_count)
        assert indices == expected

    def test_pre_execute_with_no_key_statements(self, generate_task, mock_context, mock_statement):
        """Test pre_execute when there are no KeyStatements."""
        # No KeyStatements in sub_statements
        mock_statement.sub_statements = []

        # Mock task util
        task_util = MagicMock()
        mock_context.class_factory_util.get_task_util_cls.return_value = task_util

        # Execute
        generate_task.pre_execute(mock_context)

        # Verify
        task_util.get_task_by_statement.assert_not_called()

    @pytest.mark.skip("Need rework with ray")
    def test_execute_inner_generate(self, generate_task, mock_context, mock_statement):
        """Test execute method when called from an inner generate statement."""
        # Set context not to be SetupContext
        mock_context = MagicMock(spec=GenIterContext)
        mock_context.root = MagicMock()
        mock_context.report_logging = False

        with (
            patch.object(generate_task, "_determine_count", return_value=10) as mock_determine_count,
            patch.object(generate_task, "_sp_generate", return_value={"test_full_name": ["data"]}) as mock_sp_generate,
        ):
            result = generate_task.execute(mock_context)
            assert result == {"test_full_name": ["data"]}
            mock_determine_count.assert_called_once_with(mock_context)
            mock_sp_generate.assert_called_once_with(mock_context, 0, 10)

    def test_execute_exception_handling(self, generate_task, mock_context):
        """Test that execute method handles exceptions gracefully."""
        with (
            patch.object(generate_task, "_determine_count", side_effect=Exception("Test exception")),
            pytest.raises(Exception, match="Test exception"),
        ):
            generate_task.execute(mock_context)
