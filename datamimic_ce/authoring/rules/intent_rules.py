"""Intent-model advisories that must run before the XML-only linter."""

import json
from collections.abc import Iterable

from datamimic_ce.authoring.contracts import CompilePlan, MemstoreRelationshipPlan
from datamimic_ce.authoring.derived_facts import derive_facts
from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.rules.base import IntentLintContext, IntentRule
from datamimic_ce.authoring.script_semantics import (
    ScriptScope,
    current_scope_reference,
    is_exact_scope_field_reference,
    references_current_scope_field,
)
from datamimic_ce.authoring.spec import (
    AuthoringSpecV1,
    FileExportTarget,
    ForeignKeyRole,
    GeneratedProduct,
    MemstoreSource,
    MemstoreTarget,
    ProductIntent,
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
                    parent_key_roles = tuple(
                        role
                        for role in field.roles
                        if isinstance(role, ForeignKeyRole) and role.parent_product == product.name
                    )
                    if not parent_key_roles:
                        continue
                    if isinstance(field, ScriptField) and all(
                        is_exact_scope_field_reference(field.script, ScriptScope.PARENT, role.parent_field)
                        for role in parent_key_roles
                    ):
                        continue
                    parent_fields = ", ".join(
                        f"{role.parent_product}.{role.parent_field}" for role in parent_key_roles
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
                            f'Use script: "parent.{parent_key_roles[0].parent_field}" '
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


class ProductMustHaveDeliveryTargetRule(IntentRule):
    definition = authoring_rule_definition("DM407")

    def check(self, ctx: IntentLintContext, spec: AuthoringSpecV1, _plan: CompilePlan) -> Iterable[Diagnostic]:
        # nested_list rows serialize inside their product, so only products (root and child) are checked
        products: list[tuple[str, ProductIntent]] = []
        for product_index, product in enumerate(spec.products):
            products.append((f"/products/{product_index}", product))
            if isinstance(product, GeneratedProduct):
                products += [
                    (f"/products/{product_index}/children/{child_index}", child)
                    for child_index, child in enumerate(product.children)
                ]
        # No file_export anywhere = in-memory model: verified certifies the bounded run only
        if not any(isinstance(target, FileExportTarget) for _path, entry in products for target in entry.targets):
            return
        for path, entry in products:
            if entry.targets:
                continue
            yield ctx.diag(
                ProductMustHaveDeliveryTargetRule,
                path=path,
                name=entry.name,
                evidence=f"the spec exports files, but {entry.name} declares no targets; its rows are never written",
                fix_context=f'Add e.g. {{"kind":"file_export","format":"JSON"}} to {entry.name}.targets.',
            )


class MemstoreTargetMustHaveConsumerRule(IntentRule):
    definition = authoring_rule_definition("DM408")

    def check(self, ctx: IntentLintContext, spec: AuthoringSpecV1, plan: CompilePlan) -> Iterable[Diagnostic]:
        facts = {(fact.producer_product, fact.id): fact for fact in derive_facts(plan).memstores}
        products: list[tuple[str, ProductIntent]] = []
        for product_index, root_product in enumerate(spec.products):
            products.append((f"/products/{product_index}", root_product))
            if isinstance(root_product, GeneratedProduct):
                products += [
                    (f"/products/{product_index}/children/{child_index}", child)
                    for child_index, child in enumerate(root_product.children)
                ]
        for product_path, entry in products:
            for target_index, target in enumerate(entry.targets):
                if not isinstance(target, MemstoreTarget):
                    continue
                fact = facts[(entry.name, target.id)]
                if fact.has_consumer:
                    continue
                yield ctx.diag(
                    MemstoreTargetMustHaveConsumerRule,
                    path=f"{product_path}/targets/{target_index}",
                    name=target.id,
                    evidence=f"{entry.name} writes memstore '{target.id}', but no product reads it",
                )


RULES: tuple[type[IntentRule], ...] = (
    NestedForeignKeyMustCopyParentRule,
    MemstoreReadbackFieldMustCopySourceRule,
    ProductMustHaveDeliveryTargetRule,
    MemstoreTargetMustHaveConsumerRule,
)
