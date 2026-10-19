# Connected Platform project

Use the already configured project-scoped DATAMIMIC MCP connection. Read its
server instructions and discover the current tools/capabilities before choosing
operations. The server owns workflow sequencing, document identity, execution
state and remote writes. CE command names and CE-only fields do not define the
Platform contract.

If a connection is missing, use the Platform's project connection instructions:
[Connect an MCP client](https://docs.datamimic.io/advanced/connect-mcp-client/).
Interactive Codex/Claude connections use the selected project's OAuth setup.
Verify the project identity with a non-mutating call before making changes.
Keep credentials in the host's secret storage.

For an existing model, read its current content and returned file reference/ETag.
Submit the user's intended change with the current concurrency reference. On a
conflict, reread and reconcile the change before resubmitting.

Follow the Build lifecycle advertised by the server. When it returns Pending,
poll that same execution to a terminal result. When Ready requires a separate
commit, commit the returned execution identity through the project tool. Persist
or execute only through the remote project's operations, with current references.
A rejected or expired execution cannot be committed.

Local filesystem writes and the CE CLI do not update the remote project. If the
requested operation or proof is unsupported, retain that requirement and report
the blocker. Never change the requested dataset merely to obtain Ready.
