# Amendment 23: publish IO row conversion exactly

Date: 2026-09-28. Astra decision during exporter migration.

Runtime converts XML rows before incrementing a page counter or writing a
parent/child product. IO owns that representation conversion. The original
parent IO contract omitted its public function, while the nested core contract
published the whole module.

Publish only `engine.io.exporters.core.serialization:convert_xml_dict_to_json_dict`
at both boundaries. Keep the existing `io.api` re-export and execution order.
No wrapper, callback, ownership move or dependency permission is added.
Conversion failure must leave the page counter and outputs unchanged.
