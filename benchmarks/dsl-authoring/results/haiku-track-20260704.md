# Haiku 4.5 track (agentic conditions), 2026-07-04

Raw scores and rule ids: `haiku-track-20260704.json` (grader-produced; the h1
iteration counts in it are the agent's self-report, marked as such).

Same 6 tasks as the Ollama matrix, run as agent conditions instead of single-shot
prompts, graded independently by the controller with the same 0/1/2 scoring
(lint, dry-run, intent). One adjudication: branch_fk H1 used a nested
`<nestedKey type="list">` shape with a correct join; the flat-only grader
under-scored it, manual adjudication sets it to 2 (the harness intent check
accepts both shapes since the same day).

| condition | runs | intent-correct |
|---|---|---|
| H0 bare (no tools, no repo access, single shot) | 0/6 | 0/6 |
| H1 tool loop (reference, lint, dry-run, iterate) | 6/6 | 6/6 |

H0 failures were uniformly invented vocabulary (DM101 unknown element, DM103
unknown attribute, DM104 missing required): the DSL is not usable from model
training knowledge alone, for a capable model either. H1 needed at most 2
lint iterations per task; 4 of 6 were green first try.

Read together with the Ollama matrix: static prompt material lifts weak local
models from 0/6 to at best 3/6 single-shot; the iterative tool loop lifts a
capable small model to 6/6. The diagnostics loop is worth more than any static
prompt content.
