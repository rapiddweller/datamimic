# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.TASK_ARRAY_SCRIPT_ELEMENT_TYPE,
        name="TASK_ARRAY_SCRIPT_ELEMENT_TYPE",
        title="Task Array Script Element Type",
        template=(
            "Failed while evaluate script '{script}' of <array> '{name}': expect array element "
            "datatypes in ({valid_types}), but got invalid datatype '{element_type}'"
        ),
        cause=(
            "The system failed while evaluate script '{script}' of <array> '{name}': expect array "
            "element datatypesin({valid_types}), but got invalid datatype '{element_type}'."
        ),
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_ARRAY_SCRIPT_MIXED_TYPES,
        name="TASK_ARRAY_SCRIPT_MIXED_TYPES",
        title="Task Array Script Mixed Types",
        template=(
            "Failed while evaluate script '{script}' of <array> '{name}': all elements in list "
            "must be the same data type"
        ),
        cause=(
            "The system failed while evaluate script '{script}' of <array> '{name}': all elements "
            "in list must be thesamedata type."
        ),
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_ARRAY_SCRIPT_NOT_LIST,
        name="TASK_ARRAY_SCRIPT_NOT_LIST",
        title="Task Array Script Not List",
        template=(
            "expect datatype list of evaluated script '{script}' of <array> '{name}', but got "
            "invalid datatype '{value_type}'"
        ),
        cause="A value expected to be a list was not a list in the task configuration.",
        resolution="Provide a list value for the script.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_UNKNOWN_CONVERTER,
        name="TASK_UNKNOWN_CONVERTER",
        title="Task Unknown Converter",
        template=(
            "Unknown converter '{class_name}' for {element_label}. If this is a custom converter, "
            "ensure it is registered or use a fully qualified path."
        ),
        cause=(
            "The configuration references an unknown converter '{class_name}' for {element_label}."
            " If this is acustomconverter, ensure it is registered or use a fully qualified path."
        ),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_SCRIPT_ERROR,
        name="TASK_SCRIPT_ERROR",
        title="Task Script Error",
        template="Script error in {element_label}{descriptor}: {error}",
        cause="An error occurred during task configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_SOURCE_MISSING,
        name="TASK_NESTEDKEY_SOURCE_MISSING",
        title="Task NestedKey Source Missing",
        template="Cannot load original data for <nestedKey> '{name}'",
        cause="The system could not load original data for <nestedKey> '{name}'.",
        resolution="Provide the required source and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_SCRIPT_TYPE,
        name="TASK_NESTEDKEY_SCRIPT_TYPE",
        title="Task NestedKey Script Type",
        template=(
            "Expect evaluated datatype of script '{script}' for <nestedKey> '{name}' is 'list' or "
            "'dict', but got invalid datatype: '{value_type}'"
        ),
        cause="An error occurred during task configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_RESULT_TYPE,
        name="TASK_NESTEDKEY_RESULT_TYPE",
        title="Task NestedKey Result Type",
        template=(
            "Expect evaluated datatype of script '{script}' for <nestedKey> '{name}' is 'list' or "
            "'dict', but got invalid datatype: '{value_type}'"
        ),
        cause="An error occurred during task configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_INVALID_SOURCE,
        name="TASK_NESTEDKEY_INVALID_SOURCE",
        title="Task NestedKey Invalid Source",
        template="Invalid source '{source}' of <nestedKey> '{name}'",
        cause="The configuration provides an invalid source '{source}' of <nestedKey> '{name}'.",
        resolution="Correct the source to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_DICT_SOURCE_UNSUPPORTED,
        name="TASK_NESTEDKEY_DICT_SOURCE_UNSUPPORTED",
        title="Task NestedKey Dict Source Unsupported",
        template="Source of <nestedKey> '{name}' having type 'dict' does not support format {source}",
        cause="The task configuration specifies an unsupported configuration.",
        resolution="Use a supported source or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_SOURCE_UNSUPPORTED,
        name="TASK_NESTEDKEY_SOURCE_UNSUPPORTED",
        title="Task NestedKey Source Unsupported",
        template="Cannot load data from source '{source}' of <nestedKey> '{name}'",
        cause="The system could not load data from source '{source}' of <nestedKey> '{name}'.",
        resolution="Use a supported source or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_NESTEDKEY_ITEM_NOT_DICT,
        name="TASK_NESTEDKEY_ITEM_NOT_DICT",
        title="Task NestedKey Item Not Dict",
        template=(
            "Expect current product of <nestedKey> '{name}' is a dictionary, but got invalid datatype: '{value_type}'"
        ),
        cause="A value expected to be a dictionary was not a dictionary in the task configuration.",
        resolution="Provide a dictionary value for the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_ASSERT_FAILED,
        name="TASK_ASSERT_FAILED",
        title="Task Assert Failed",
        template="<assert> failed: condition {condition} is not true{extra}",
        cause="An <assert> invariant did not hold for the setup context or a generated record.",
        resolution="Correct the generation logic or the assertion so the condition holds.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_KEY_WEIGHTS_LENGTH,
        name="TASK_KEY_WEIGHTS_LENGTH",
        title="Task Key Weights Length",
        template=(
            "<{element_tag} '{name}'> needs one weight per value: {weight_count} weights vs {value_count} values"
        ),
        cause="The number of <key/variable weights=> entries does not match the number of values.",
        resolution="Provide exactly one weight per value, or remove weights for a uniform pick.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_KEY_WEIGHTS_NOT_NUMERIC,
        name="TASK_KEY_WEIGHTS_NOT_NUMERIC",
        title="Task Key Weights Not Numeric",
        template="<{element_tag} '{name}'> weights must be comma-separated numbers, got {weights}",
        cause="A <key/variable weights=> entry could not be parsed as a number.",
        resolution='Use comma-separated numeric weights, e.g. weights="0.7,0.2,0.1".',
    ),
    IssueDefinition(
        code=IssueCode.TASK_KEY_UNIQUE_EXHAUSTED,
        name="TASK_KEY_UNIQUE_EXHAUSTED",
        title="Task Key Unique Exhausted",
        template=(
            "<{element_tag} '{name}' unique> exhausted: only {distinct_count} distinct values, "
            "reduce count or add more values."
        ),
        cause="A <key/variable unique> was asked for more records than it has distinct values.",
        resolution="Reduce the generated count or provide more distinct values.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_REFERENCE_ORDERED_EXHAUSTED,
        name="TASK_REFERENCE_ORDERED_EXHAUSTED",
        title="Task Reference Ordered Exhausted",
        template=(
            "Ordered reference '{name}' exhausted after {count} rows; add cyclic=\"true\" to wrap, "
            "or reduce the generated count."
        ),
        cause='A non-cyclic distribution="ordered" <reference> was walked past its last candidate.',
        resolution='Add cyclic="true" to wrap, or reduce the generated count.',
    ),
    IssueDefinition(
        code=IssueCode.TASK_VARIABLE_STORAGE_UNRESOLVABLE_SOURCE,
        name="TASK_VARIABLE_STORAGE_UNRESOLVABLE_SOURCE",
        title="Task Variable Storage Unresolvable Source",
        template=(
            "<variable '{name}' storage='{storage}'> source '{source}' has no stable pool to "
            "materialize (not a file/database/memstore source)."
        ),
        cause=(
            "storage= requires a source that resolves to a materializable pool up front; "
            "'{source}' resolves dynamically at task runtime (e.g. it names another <variable>)."
        ),
        resolution="Remove storage= or point source at a file, database table, or memstore.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_KEY_SCRIPT_INVALID_TYPE,
        name="TASK_KEY_SCRIPT_INVALID_TYPE",
        title="Task Key Script Invalid Type",
        template="<key> '{name}' expects simple data type, but got type '{value_type}'",
        cause="The script value is invalid for the task configuration.",
        resolution="Correct the script to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_VARIABLE_SELECTOR_ONLY_DB,
        name="TASK_VARIABLE_SELECTOR_ONLY_DB",
        title="Task Variable Selector Only DB",
        template="<variable> '{name}': 'selector' only works with 'source' database (MongoDB, SQL)",
        cause="An error occurred during task configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_VARIABLE_SOURCE_UNSUPPORTED,
        name="TASK_VARIABLE_SOURCE_UNSUPPORTED",
        title="Task Variable Source Unsupported",
        template="Cannot get data from source '{source}' of <variable> '{name}'",
        cause="The system could not get data from source '{source}' of <variable> '{name}'.",
        resolution="Use a supported source or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_EXPRESSION_EVAL_FAILED,
        name="TASK_EXPRESSION_EVAL_FAILED",
        title="Task Expression Eval Failed",
        template="Failed to evaluate expression '{expr}': {error}",
        cause="The system failed to evaluate expression '{expr}': {error}.",
        resolution="Fix the expression or script and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_VALUES_INVALID,
        name="TASK_VALUES_INVALID",
        title="Task Values Invalid",
        template="Invalid values list for <{element_tag}> '{name}': {values}",
        cause=("The configuration provides an invalid values list for <{element_tag}> '{name}': {values}."),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_WEIGHTED_SOURCE_INVALID,
        name="TASK_WEIGHTED_SOURCE_INVALID",
        title="Task Weighted Source Invalid",
        template="Data source of {element_label} must be type of: 'wgt.csv'",
        cause=(
            "The configuration violates the requirement that Data source of {element_label} must be type of: 'wgt.csv'."
        ),
        resolution="Correct the source to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_PATTERN_MISSING,
        name="TASK_PATTERN_MISSING",
        title="Task Pattern Missing",
        template="Pattern is missing for <{element_tag}> '{name}'",
        cause="A required pattern is missing in the task configuration.",
        resolution="Provide the required pattern and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_GENERATION_MODE_UNKNOWN,
        name="TASK_GENERATION_MODE_UNKNOWN",
        title="Task Generation Mode Unknown",
        template="Cannot find data generation mode for <{element_tag}> '{name}'",
        cause="The system could not find data generation mode for <{element_tag}> '{name}'.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_CONVERTER_FAILED,
        name="TASK_CONVERTER_FAILED",
        title="Task Converter Failed",
        template="Failed to generate data for <{element_tag}> '{name}': {error}",
        cause="The system failed to generate data for <{element_tag}> '{name}': {error}.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_DATATYPE_INVALID,
        name="TASK_DATATYPE_INVALID",
        title="Task Datatype Invalid",
        template=(
            "Failed to convert datatype for <{element_tag}> '{name}'. Expect datatype {expected} but get '{data_type}'"
        ),
        cause=(
            "The system failed to convert datatype for <{element_tag}> '{name}'. Expect datatype "
            "{expected} butget'{data_type}'."
        ),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_REFERENCE_UNSUPPORTED_SOURCE,
        name="TASK_REFERENCE_UNSUPPORTED_SOURCE",
        title="Task Reference Unsupported Source",
        template=(
            "Reference '{name}' requires a configured relational or MongoDB source, or a "
            ".wgt.csv/.wgt.ent.csv project file"
        ),
        cause=("The reference source is neither a supported configured client nor a weighted project file."),
        resolution=("Use a relational or MongoDB source id, or provide a .wgt.csv/.wgt.ent.csv project file."),
    ),
    IssueDefinition(
        code=IssueCode.TASK_REFERENCE_NO_DATA,
        name="TASK_REFERENCE_NO_DATA",
        title="Task Reference No Data",
        template="No data found for reference '{name}'",
        cause="An error occurred during task configuration.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_WHILE_MAX_ITERATIONS_EXCEEDED,
        name="TASK_WHILE_MAX_ITERATIONS_EXCEEDED",
        title="Task While Loop Max Iterations Exceeded",
        template=(
            "<while> exceeded max_iterations={max_iterations}: condition '{condition}' never "
            "became false (possible infinite loop)."
        ),
        cause="The loop condition remained true after reaching the maximum iteration limit.",
        resolution=(
            "Verify the loop condition and ensure it eventually becomes false, or increase maxIterations if needed."
        ),
    ),
    IssueDefinition(
        code=IssueCode.GENERATE_OFFSET_UNSUPPORTED_MEMSTORE,
        name="GENERATE_OFFSET_UNSUPPORTED_MEMSTORE",
        title="Generate Offset Unsupported for Memstore",
        template=("<generate> '{stmt_name}': offset= is only supported for file sources, not memstore '{source_str}'."),
        cause=(
            "The offset attribute cannot be used with memstore/product sources; it only applies to file-based sources."
        ),
        resolution="Remove the offset attribute, or use a file source instead of memstore.",
    ),
    IssueDefinition(
        code=IssueCode.GENERATE_OFFSET_UNSUPPORTED_DATABASE_CLIENT,
        name="GENERATE_OFFSET_UNSUPPORTED_DATABASE_CLIENT",
        title="Generate Offset Unsupported for Database Client",
        template=(
            "<generate> '{stmt_name}': offset= is only supported for file sources, not database "
            "client '{source_str}' - use a selector with an SQL/Mongo skip instead."
        ),
        cause=(
            "The offset attribute cannot be used with database client sources; it only applies to file-based sources."
        ),
        resolution="Remove the offset attribute, or use a file source instead of a database client.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_ENTITY_NOT_FOUND,
        name="TASK_ENTITY_NOT_FOUND",
        title="Task Entity Not Found",
        template="Entity name '{entity_name}' not found in the XML model",
        cause="The referenced entity could not be found for the task configuration.",
        resolution="Ensure the referenced entity exists and the identifier/path is correct.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_COUNT_ABOVE_BOUNDED_LIMIT,
        name="TASK_COUNT_ABOVE_BOUNDED_LIMIT",
        title="Task Count Above Bounded Limit",
        template="count evaluated to {count}, above the bounded per-invocation limit {limit}",
        cause="A runtime count exceeded the per-invocation limit of bounded Authoring execution.",
        resolution="Raise max_count to at least the evaluated count, or lower the count expression.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_TOTAL_ROW_BUDGET_EXCEEDED,
        name="TASK_TOTAL_ROW_BUDGET_EXCEEDED",
        title="Task Total Row Budget Exceeded",
        template="generated product rows exceed the total Build limit {limit}",
        cause="The run attempted to generate more product rows than its shared total-row limit.",
        resolution=(
            "Build derives max_count only when every product has a literal count or reads a memstore back from a "
            'literal producer. Otherwise add "max_count": <the rows of all products together> at the top level '
            'of acceptance/build.json, beside "expectations" (authoring run and dry-run take --max-count). A higher '
            'value is safe, up to the Build ceiling: if you do not know the total, set "max_count": 2000. Or reduce '
            "the rows."
        ),
    ),
    IssueDefinition(
        code=IssueCode.TASK_COUNT_SELECTOR_UNSUPPORTED_CLIENT,
        name="TASK_COUNT_SELECTOR_UNSUPPORTED_CLIENT",
        title="Task Count Selector Unsupported Client",
        template="Using selector without count only supports DatabaseClient (MongoDB, Relational Database)",
        cause="The task configuration specifies an unsupported client.",
        resolution="Use a supported client or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_MP_PLATFORM_UNSUPPORTED,
        name="TASK_MP_PLATFORM_UNSUPPORTED",
        title="Task MP Platform Unsupported",
        template="Multiprocessing platform '{mp_platform}' of <generate> '{stmt_name}' is not supported",
        cause="The mpPlatform value is not supported by the runtime.",
        resolution="Use multiprocessing or ray (or omit to use multiprocessing).",
    ),
    IssueDefinition(
        code=IssueCode.TASK_EXECUTE_CLIENT_NOT_FOUND,
        name="TASK_EXECUTE_CLIENT_NOT_FOUND",
        title="Task Execute Client Not Found",
        template="Client '{client_id}' not found for <execute> task. Check your project environment configuration.",
        cause="The referenced client could not be found for the task configuration.",
        resolution="Ensure the referenced client exists and the identifier/path is correct.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_EXECUTE_SCRIPT_NOT_FOUND,
        name="TASK_EXECUTE_SCRIPT_NOT_FOUND",
        title="Task Execute Script Not Found",
        template=(
            "Script file '{script_name}' not found in task workspace. "
            "Check your project environment configuration or uploaded script assets."
        ),
        cause="The referenced script could not be found for the task configuration.",
        resolution="Ensure the referenced script exists and the identifier/path is correct.",
    ),
    IssueDefinition(
        code=IssueCode.TASK_EXECUTE_BASH_FAILED,
        name="TASK_EXECUTE_BASH_FAILED",
        title="Task Execute Bash Failed",
        template="<execute type='bash'> failed (exit {exit_code}): {detail}",
        cause="The shell command run by <execute type='bash'> returned a non-zero exit status.",
        resolution="Fix the shell command or its environment; inspect the reported stderr/exit code.",
    ),
]
