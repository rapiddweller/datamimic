# Amendment 56: keep exporter internals behind IO

Date: 2026-09-28.

`consume_exporters` and `convert_xml_dict_to_json_dict` are used only by IO's
exporter registry. Remove them from the IO facade; keep their implementations
and dispatch behavior unchanged. This removes three old facade type findings.

`ExportSession.prepare_page` still accepts raw row payloads. ArchKeel class-method
coverage is under separate audit, so this change does not establish a green target.
