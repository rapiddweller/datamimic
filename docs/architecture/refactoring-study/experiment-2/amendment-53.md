# Amendment 53: publish buffered lifecycle operations from IO

Date: 2026-09-28.

The frozen IO contract exposes exporter construction but not the buffered
finalization and publication operations used by Runtime. Runtime therefore
reconstructed concrete exporters and checked their classes. Publish two typed
IO operations for these existing phases. Runtime keeps worker selection,
statement traversal, and the order: finalize all, then publish all.

This adds two IO interface entries. It changes no dependency direction or
descriptor behavior. The known conditional-child artifact bug is not fixed by
this amendment; see `step-14-export-lifecycle.md`.
