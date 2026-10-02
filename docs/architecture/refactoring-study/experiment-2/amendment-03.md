# Amendment 03: packaged domain datasets cross a narrow IO facet

## Decision

Allow `domains` to require `io` only through `engine.io.dataset_api`. That surface exports file
loading and caching, not database clients.

## Evidence

- 29 domain modules read packaged CSV or JSON datasets.
- The contents, fallback rules, and weighted selection are domain behavior.
- Parsing and caching are already owned by `engine.io`; copying them into `domains` would create a
  second implementation.
- `complete_requires.through` keeps the existing pagination and database imports as violations.

## Why this is a correction

The frozen target treated every `domains -> io` edge as wrong. That confused domain ownership of
the data with ownership of file parsing. A narrow facet states both decisions without adding a
shared foundation package or allowing database access from domains.
