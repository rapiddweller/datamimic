# Amendment 46: move expression evaluation policy to scripting

Date: 2026-09-28.

`Context` keeps namespace assembly, scope aliases, merge precedence, and seeded
`expression_globals` construction. `scripting/evaluation.py` owns evaluation of
those globals/locals, result normalization, forbidden-result checks, colon
syntax retry, error translation, and `DotableDict`. Callers import
`DotableDict` from scripting directly; do not retain an alias in contexts.
Preserve shallow list normalization, ValueError messages/chaining, retry
asymmetry, and one evaluation on each success path.
