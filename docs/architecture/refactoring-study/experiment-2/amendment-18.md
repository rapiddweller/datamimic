# Amendment 18: do not invent descriptor context

Date: 2026-09-25. Status: proposed for architect review in Draft PR #274.

The inner target proposed `errors/context/` to mirror EE. CE already reports XML path and line
through Authoring diagnostics, but no current CE consumer reads a structured location from a
parser exception. Three implementations were rejected:

- Adding location text changes frozen descriptor error messages and embeds temporary paths.
- A `ValueError` subclass changes the recorded error type for at least 39 parser-failing descriptors.
- Attaching an attribute violates `NO-MAGIC-CONTROL-FLOW`; a typed cause changes traceback
  chaining and hides the original validation cause in normal rendering.

Do not ship an empty package or weaken the rule. The CE target requires real shared codes,
types, catalog, factory, and formatter, but defers `errors/context/` until an API consumes it
and an error-chain contract can be tested. EE keeps its existing context owner. This is a
physical-parity exception, not a claim that CE and EE already have identical errors.
