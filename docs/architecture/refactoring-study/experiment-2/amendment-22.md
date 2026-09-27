# Amendment 22: exporter entry points, not another utility class

Date: 2026-09-28. Astra decision before exporter implementation.

The parent IO contract declared a future `ExporterUtil` class, but its nested
contract declared functions. Use the existing registry owner and expose
`create_exporter_list`, `consume_exporters`, `buffered_exporter_names` and
`smoke_export`. Move the live target-argument parser to `core/routing.py` and
publish it for Authoring. Remove the old utility class without a path shim.

The old `json_dumps`, `custom_serializer`, `SupportsAsPy` and
`check_path_format` have no production callers; delete them and their tests
instead of relocating dead APIs. Keep the JSON exporter's different encoder
unchanged. `core/serialization.py` still receives the live XML-row conversion
from `TaskUtil`, not from the deleted utility methods. The target file count
remains 495. XML descriptors, output semantics and prior baselines are frozen.
