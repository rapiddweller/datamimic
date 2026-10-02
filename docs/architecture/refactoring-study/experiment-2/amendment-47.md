# Amendment 47: define value-task leaves

Date: 2026-09-28.

Mount six semantic children under `TASKS-VALUES`: shared key/variable base,
scalar, structured, reference, variable and construction. Move variable entity
service creation into `construction/entity.py`; keep constructor syntax parsing
in `entity_constructor.py`. Preserve source selection, seeded generation and
task behavior.

Expose `BaseDomainService` through the existing `domains.api` facade for the
construction function's return type.
