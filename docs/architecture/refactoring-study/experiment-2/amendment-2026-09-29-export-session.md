# Amendment: separate exporter session ownership

The exporter registry contract combined target-string construction with
per-worker registration and page dispatch. Astra's bounded correction assigns
the latter to `engine/io/exporters/session.py`; it constructs exporters through
the registry, while the registry has no reverse session dependency. The public
`io.api.ExportSession` entry and runtime behavior remain unchanged. The source
map records both origins: `exporter_util.py` for construction and `task_util.py`
for operation/page dispatch.
