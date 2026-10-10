# Amendment 49: narrow unused authoring helper entries

Date: 2026-09-28.

Remove five rule-module entries and two adapter-module entries from the
authoring public declaration. They are internal implementation modules, not
independent cross-component APIs. Keep their source and module responsibility
declarations. This does not decide the remaining unused entries, including
public transport, DSL, domain, runtime or IO surfaces.
