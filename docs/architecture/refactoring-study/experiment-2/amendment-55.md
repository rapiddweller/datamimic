# Amendment 55: distinguish external entry points from sibling APIs

Date: 2026-09-28.

The CLI and MCP are installed commands, not APIs imported by sibling components.
Keep them in `public_commands`; remove their unused component-local `public`
entries. `generate_domain` is a documented Python API in the README, so declare
it once in root `public_api` instead of twice as a sibling interface. Its
`JsonObject` return alias is part of that external signature.

This changes declarations only. It does not remove a module, alter a command,
or change descriptor behavior. Other unused-entry diagnostics remain visible
until their external promises and local consumers are reviewed individually.
