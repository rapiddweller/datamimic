# Amendment 68: explicit environment startup

Date: 2026-09-29. Decision: Astra, after independent QA of CE entrypoints.

Root package import must not load `.env` or mutate the process environment.
CLI and MCP executables load startup-cwd `.env` with `override=False` before
importing the application graph or resolving settings, host, port or auth
defaults. Python, Domain and Authoring
library callers own environment preparation; Runtime settings resolve on use.
Descriptor `.env.properties` selection is unchanged. This intentionally
supersedes the prior import-time dotenv compatibility decision for CE 5.0.

Acceptance requires subprocess checks for import purity, executable startup
order, explicit-env precedence, Domain/MCP behavior, and seeded descriptor
output under the same explicit environment. No new bootstrap framework or
legacy import path is part of the target.
