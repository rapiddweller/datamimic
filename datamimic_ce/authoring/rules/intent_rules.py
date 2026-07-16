"""Intent-model advisories that must run before the XML-only linter."""

from collections.abc import Iterable

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.rules.base import IntentLintContext, IntentRule
from datamimic_ce.authoring.spec import AuthoringSpecV1, ForeignKeyRole, GeneratedProduct, ScriptField


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


RULES: tuple[type[IntentRule], ...] = (NestedForeignKeyMustCopyParentRule,)
