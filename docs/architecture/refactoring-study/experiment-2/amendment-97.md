# Amendment 97: four existing namespace owners

2026-10-05. Astra, delegated architect; base `b55980c3`.

Assign exact initializers to existing concerns, without claiming descendants:

| Namespace | Inner owner | Reason |
|---|---|---|
| `domains.finance` | FINANCE-MODELS | Re-exports four model classes. |
| `domains.healthcare` | HEALTHCARE-SERVICES | Composes model and service exports. |
| `engine.io.exporters` | EXPORTERS-CORE | Stewardship by the common exporter interface. |
| `domains.shared.converters` | CONVERTERS-BASE | Stewardship by the common converter interface. |

Namespaces above are relative to `datamimic_ce`. The last two are inert markers;
ownership does not invent behavior. Luna challenged the exporter choice. Astra
retained `IO -> IO-EXPORTERS -> EXPORTERS-CORE`: the parent already owns the
subtree, while its mounted contract needs an exact child owner. Assigning the
marker to IO-API would overlap the parent boundary and leave the inner gap.

Change only `exact_modules` and each owner's English responsibility sentence.
Preserve package selectors, child owners, public entries, requires and rules.
No source, exports, XML, baseline, allowance, oracle, gate or checker changes.

Six initializer findings remain. Errors' proposed factory ownership is blocked:
the released checker reports its proven root-re-exported function as unused
after that assignment. Preserve the finding and public contract until the
checker is corrected ([ArchKeel #338](https://github.com/rapiddweller/archkeel/issues/338));
do not change imports or permissions to hide it.
Evidence: [Step 105](step-105-namespace-owners.md).
