"""Intent-model advisories that must run before the XML-only linter."""

from collections.abc import Iterable

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.rules.base import IntentLintContext, IntentRule
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

    def check(self, ctx: IntentLintContext, spec: AuthoringSpecV1) -> Iterable[Diagnostic]:
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

    def check(self, ctx: IntentLintContext, spec: AuthoringSpecV1) -> Iterable[Diagnostic]:
        for product_index, product in enumerate(spec.products):
            if not isinstance(product, SourceProduct) or not isinstance(product.source, MemstoreSource):
                continue
            producer_name = product.source.product
            if producer_name is None:
                continue
            producer = next((candidate for candidate in spec.products if candidate.name == producer_name), None)
            if producer is None:
                continue
            producer_field_names = {field.name for field in producer.fields}
            for field_index, field in enumerate(product.fields):
                if field.name not in producer_field_names:
                    continue
                if isinstance(field, ScriptField) and field.script == f"this.{field.name}":
                    continue
                yield ctx.diag(
                    MemstoreReadbackFieldMustCopySourceRule,
                    path=f"/products/{product_index}/fields/{field_index}",
                    name=field.name,
                    evidence=(
                        f"{product.name}.{field.name} reads memstore '{product.source.id}' "
                        f"from {product.source.product!r} with kind '{field.kind}'"
                    ),
                    fix_context=(
                        f'Replace it with {{"kind":"script","name":"{field.name}",'
                        f'"script":"this.{field.name}"}}.'
                    ),
                )


RULES: tuple[type[IntentRule], ...] = (
    NestedForeignKeyMustCopyParentRule,
    MemstoreReadbackFieldMustCopySourceRule,
)
