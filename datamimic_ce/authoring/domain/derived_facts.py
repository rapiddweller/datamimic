# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Project compiler-owned facts into the stable scaffold result contract."""

from datamimic_ce.authoring.contracts import (
    CompilePlan,
    DerivedFacts,
    DerivedForeignKeyFact,
    DerivedMemstoreFact,
    DerivedProductFact,
    ForeignKeyRolePlan,
    MemstoreRelationshipPlan,
    MemstoreTargetBindingPlan,
    TimeSeriesProductCompilePlan,
)


def derive_facts(plan: CompilePlan) -> DerivedFacts:
    """Return only facts directly established by the validated compiler plan."""

    consumers_by_binding: dict[tuple[str, str], list[str]] = {}
    for relationship in plan.relationships:
        if isinstance(relationship, MemstoreRelationshipPlan):
            consumers_by_binding.setdefault(
                (relationship.parent, relationship.source_id), []
            ).append(relationship.child)

    products = [
        DerivedProductFact(
            name=product.name,
            kind=product.kind,
            row_count=product.static_count,
            series_count=(product.series_count if isinstance(product, TimeSeriesProductCompilePlan) else None),
        )
        for product in plan.products
    ]
    memstores = [
        DerivedMemstoreFact(
            id=target.id,
            producer_product=product.name,
            consumer_products=consumers_by_binding.get((product.name, target.id), []),
            has_consumer=bool(consumers_by_binding.get((product.name, target.id), [])),
        )
        for product in plan.products
        for target in product.targets
        if isinstance(target, MemstoreTargetBindingPlan)
    ]

    foreign_keys: list[DerivedForeignKeyFact] = []
    seen_foreign_keys: set[tuple[str, str, str, str]] = set()
    for product in plan.products:
        for field in product.fields:
            for role in field.roles:
                if not isinstance(role, ForeignKeyRolePlan):
                    continue
                fact = (product.name, field.name, role.parent_product, role.parent_field)
                if fact in seen_foreign_keys:
                    continue
                seen_foreign_keys.add(fact)
                foreign_keys.append(
                    DerivedForeignKeyFact(
                        child_product=product.name,
                        child_field=field.name,
                        parent_product=role.parent_product,
                        parent_field=role.parent_field,
                    )
                )
    return DerivedFacts(products=products, memstores=memstores, foreign_keys=foreign_keys)
