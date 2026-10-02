# Amendment 48: split Runtime source adapters

Keep `engine/runtime/tasks/sources/` flat. Replace the mixed `router.py` with
`generate.py`, `nested.py`, `reference.py` and `length.py`; retain
`variable.py`, `chunk_source_reader.py` and `__init__.py`. Update every caller
and test patch target. Do not add a `router.py` compatibility shim.

The nested ArchKeel contract assigns each operation module, its public adapter
operations, local dependencies and exact package layout. Runtime resolves
statement and context state; IO/data_sources retains generic read and selection
policy. No behavior or seed timing changes are part of this slice.
