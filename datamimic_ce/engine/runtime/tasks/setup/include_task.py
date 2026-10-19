# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pathlib import Path

from datamimic_ce.engine.dsl.api import DescriptorParser, IncludeStatement, SetupStatement, parse_properties
from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.contexts.geniter_context import GenIterContext
from datamimic_ce.engine.runtime.tasks.base.task import CommonSubTask
from datamimic_ce.errors import DescriptorLocation, IssueCode, MissingDescriptorError, include_error


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
        # A dynamic uri interpolates {var} f-string style against the context (dynamic include), so
        # a path like "{database}/shop.{database}.properties" resolves to "h2/shop.h2.properties".
        if "{" in uri:
            escaped = uri.replace("'", "\\'").replace('"', '\\"')
            resolved_uri = ctx.evaluate_python_expression(f"f'''{escaped}'''")
            if not isinstance(resolved_uri, str):
                raise TypeError("Dynamic include URI must evaluate to a string")
            uri = resolved_uri

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
        from datamimic_ce.engine.runtime.tasks.setup.setup_task import SetupTask

        # Case 1: Check if uri is a properties file
        if uri.endswith(".properties"):
            # Import properties into context
            try:
                new_props = parse_properties(ctx.descriptor_dir / uri)
            except FileNotFoundError as error:
                raise include_error(
                    code=IssueCode.INCLUDE_FILE_NOT_FOUND,
                    uri=Path(uri).name,
                    location=DescriptorLocation("include", attribute="uri"),
                ) from error
            ctx.properties.update(new_props)
        # Case 2: Check if uri is a descriptor file
        elif uri.endswith(".xml"):
            # Parse and execute descriptor file
            sub_setup_stmt = _parse_included_descriptor(ctx, uri)
            SetupTask.execute_include(setup_stmt=sub_setup_stmt, parent_context=ctx)
        else:
            raise include_error(code=IssueCode.INCLUDE_UNSUPPORTED_FILE_TYPE, uri=uri)

    def _execute_with_geniter_context(self, ctx: GenIterContext, uri: str) -> None:
        """
        Execute the include task with geniter context (in <generate>)
        :param ctx:
        :param uri:
        :return:
        """
        root_ctx = ctx.root
        if uri.endswith(".xml"):
            from datamimic_ce.engine.runtime.tasks.setup.setup_task import SetupTask

            # Parse and execute descriptor file
            sub_setup_stmt = _parse_included_descriptor(root_ctx, uri)
            # Use copy of parent_context as child_context
            copied_root_context = SetupTask._copy_include_context(root_ctx)

            # Update root_context with attributes defined in sub-setup statement
            copied_root_context.update_with_stmt(sub_setup_stmt)
            # Update root_context with parent_context variables and current_product
            copied_root_context.global_variables.update(ctx.current_variables)
            copied_root_context.global_variables.update(ctx.current_product)

            SetupTask.execute_statements(sub_setup_stmt, copied_root_context)
        else:
            raise include_error(code=IssueCode.INCLUDE_UNSUPPORTED_FILE_TYPE_GENERATE, uri=uri)


def _parse_included_descriptor(ctx: SetupContext, uri: str) -> SetupStatement:
    try:
        statement = DescriptorParser.parse(
            ctx.descriptor_dir / uri,
            ctx.properties,
            ctx.runtime_environment,
            profile_loader=ctx.profile_loader or load_connection_profile,
        )
        if ctx.included_statement_transformer is not None:
            if statement.default_separator is None:
                statement.default_separator = ctx.default_separator
            if statement.default_line_separator is None:
                statement.default_line_separator = ctx.default_line_separator
            ctx.included_statement_transformer(statement)
        return statement
    except MissingDescriptorError as error:
        raise include_error(
            code=IssueCode.INCLUDE_FILE_NOT_FOUND,
            uri=Path(uri).name,
            location=DescriptorLocation("include", attribute="uri"),
        ) from error
