# Amendment 212 — dynamic SQL dispatch exception

2026-10-11. Decision: explicitly approved by Alex after independent Astra review.

Preserve [Amendment 155](amendment-155-execute-task-sql-capability.md): injected
SQL clients, one method lookup and unchanged native errors. The mixed client
registry cannot statically prove that an arbitrary target supports SQL.

`NO-UNPROVEN-CASTS` forbids casts everywhere except the exact
`ExecuteTask._run_sql` function. This permits every cast within that function,
including future additions. All other `NO-MAGIC-CONTROL-FLOW` bans remain there.
The existing cast remains an explicit interoperability limitation; this decision
proves neither client capability nor runtime success. Source behavior is unchanged.
