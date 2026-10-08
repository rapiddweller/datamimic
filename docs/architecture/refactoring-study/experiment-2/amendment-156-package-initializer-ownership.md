# Amendment 156 — package initializer ownership

Date: 2026-10-08. Decision: Astra-decided target clarification.

Assign the eight reviewed package-root initializers to existing inner components
with `exact_modules`; do not broaden their package selectors. Healthcare's
initializer exports models and services, so the services component owns that
package entry. Finance exports only models, so models owns it. The remaining
initializers are inert markers or package-level documentation; assign them to
the existing entry, service, or converter-interface component recorded in
`structure-review.json`.

This closes the nested `complete_assignment` gaps without adding components,
deleting package initializers, granting public exports, or changing dependency
permissions. An exact owner does not exempt the initializer from import checks.
