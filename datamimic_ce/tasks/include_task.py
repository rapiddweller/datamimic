# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.statements.include_statement import IncludeStatement
from datamimic_ce.tasks.task import CommonSubTask
from datamimic_ce.utils.file_util import FileUtil


class IncludeTask(CommonSubTask):
    """
    Include environment properties loaded from file or execute other descriptor files
    """

    def __init__(self, statement: IncludeStatement):
        self._statement = statement

    @property
    def statement(self) -> IncludeStatement:
        return self._statement

    def execute(self, ctx: SetupContext | GenIterContext) -> None:
        """
        Execute the include task
        :param ctx:
        :return:
        """
        uri = self.statement.uri
        # Evaluate uri if it is a python expression
        if uri.startswith("{") and uri.endswith("}"):
            uri = ctx.evaluate_python_expression(uri[1:-1])

        if isinstance(ctx, SetupContext):
            self._execute_with_setup_context(ctx, uri)
        else:
            self._execute_with_geniter_context(ctx, uri)

    def _execute_with_setup_context(self, ctx: SetupContext, uri: str) -> None:
        """
        Execute the include task with setup context (in <setup>)
        :param ctx:
        :param uri:
        :return:
        """
        # Case 1: Check if uri is a properties file
        if uri.endswith(".properties"):
            # Import properties into context
            new_props = FileUtil.parse_properties(ctx.descriptor_dir / uri)
            ctx.properties.update(new_props)
        # Case 2: Check if uri is a descriptor file
        elif uri.endswith(".xml"):
            from datamimic_ce.tasks.setup_task import SetupTask

            # Parse and execute descriptor file
            sub_setup_stmt = DescriptorParser.parse(
                ctx.class_factory_util,
                ctx.descriptor_dir / self.statement.uri,
                ctx.properties,
            )
            SetupTask.execute_include(setup_stmt=sub_setup_stmt, parent_context=ctx)
        else:
            raise ValueError(f"Unsupported include file type: {uri}. Only .properties and .xml are supported")

    def _execute_with_geniter_context(self, ctx: GenIterContext, uri: str) -> None:
        """
        Execute the include task with geniter context (in <generate>)
        :param ctx:
        :param uri:
        :return:
        """
        root_ctx = ctx.root
        if uri.endswith(".xml"):
            from datamimic_ce.tasks.generate_task import GenerateTask

            # Parse and execute descriptor file
            sub_geniter_stmt = DescriptorParser.parse(
                root_ctx.class_factory_util,
                root_ctx.descriptor_dir / uri,
                root_ctx.properties,
            )
            GenerateTask.execute_include(setup_stmt=sub_geniter_stmt, parent_context=ctx)
        else:
            raise ValueError(f"Unsupported include file type: {uri} inside <generate>. Only .xml is supported")
