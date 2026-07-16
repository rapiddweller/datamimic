"""Intent-model advisories that must run before the XML-only linter."""

import json
from collections.abc import Iterable

from datamimic_ce.authoring.contracts import CompilePlan, MemstoreRelationshipPlan
from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.rules.base import IntentLintContext, IntentRule
from datamimic_ce.authoring.script_semantics import current_scope_reference, references_current_scope_field
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    ForeignKeyRole,
    GeneratedProduct,
    MemstoreSource,
    ScriptField,
    SourceProduct,
)


class NestedForeignKeyMustCopyParentRule(IntentRule):
    definition = authoring_rule_definition("DM404")

    def check(self, ctx: IntentLintContext, spec: AuthoringSpecV1, _plan: CompilePlan) -> Iterable[Diagnostic]:
        for product_index, product in enumerate(spec.products):
            if not isinstance(product, GeneratedProduct):
                continue
            for child_index, child in enumerate(product.children):
                for field_index, field in enumerate(child.fields):
                    foreign_key_roles = [role for role in field.roles if isinstance(role, ForeignKeyRole)]
                    if not foreign_key_roles or isinstance(field, ScriptField):
                        continue
                    parent_fields = ", ".join(
                        f"{role.parent_product}.{role.parent_field}" for role in foreign_key_roles
                    )
                    yield ctx.diag(
                        NestedForeignKeyMustCopyParentRule,
                        path=f"/products/{product_index}/children/{child_index}/fields/{field_index}",
                        name=field.name,
                        evidence=(
                            f"{child.name}.{field.name} uses kind '{field.kind}' for foreign key(s) "
                            f"to {parent_fields}"
                        ),
                        fix_context=(
                            f'Use script: "parent.{foreign_key_roles[0].parent_field}" '
                            f"for {child.name}.{field.name}."
                        ),
                    )


class MemstoreReadbackFieldMustCopySourceRule(IntentRule):
    definition = authoring_rule_definition("DM406")

    def check(self, ctx: IntentLintContext, spec: AuthoringSpecV1, plan: CompilePlan) -> Iterable[Diagnostic]:
        source_products = {
            product.name: (product_index, product)
            for product_index, product in enumerate(spec.products)
            if isinstance(product, SourceProduct) and isinstance(product.source, MemstoreSource)
        }
        product_fields = {product.name: {field.name for field in product.fields} for product in plan.products}
        for relationship in plan.relationships:
            if not isinstance(relationship, MemstoreRelationshipPlan):
                continue
            source_product = source_products.get(relationship.child)
            if source_product is None:
                continue
            product_index, product = source_product
            producer_field_names = product_fields[relationship.parent]
            for field_index, field in enumerate(product.fields):
                if field.name not in producer_field_names:
                    continue
                if isinstance(field, ScriptField) and references_current_scope_field(field.script, field.name):
                    continue
                replacement = ScriptField(
                    name=field.name,
                    roles=field.roles,
                    script=current_scope_reference(field.name),
                )
                replacement_json = json.dumps(
                    replacement.model_dump(mode="json"),
                    separators=(",", ":"),
                )
                yield ctx.diag(
                    MemstoreReadbackFieldMustCopySourceRule,
                    path=f"/products/{product_index}/fields/{field_index}",
                    name=field.name,
                    evidence=(
                        f"{product.name}.{field.name} reads memstore '{relationship.source_id}' "
                        f"from '{relationship.parent}' with kind '{field.kind}'"
                    ),
                    fix_context=(
                        "Replace it with "
                        f"{replacement_json}."
                    ),
                )


RULES: tuple[type[IntentRule], ...] = (
    NestedForeignKeyMustCopyParentRule,
    MemstoreReadbackFieldMustCopySourceRule,
)
