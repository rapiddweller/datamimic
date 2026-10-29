# Benchmarking local Ollama models

Treat a benchmark row as valid only when its model profile has passed a
preflight. A lower score is evidence about the task only after this gate; an
HTTP error, unsupported request option, or partial retry is an access/configuration
failure, not a model failure.

1. Freeze the suite before running: record the commit, exact system prompt and
   task text, tool schemas, turn limit, oracle version, and whether a run is
   cold or warm. Set and report an Ollama inference `options.seed`; this is
   separate from the descriptor's `rngSeed`. Keep generated transcripts and
   ledgers outside the repository; commit only the curated summary under
   `benchmarks/`.
2. Snapshot every installed model with `ollama list` and `ollama show <model>`.
   Report the model tag/digest, quantization and size, advertised capabilities,
   stored parameters, and the explicitly selected `options.num_ctx`. Do not
   compare a tag whose digest or context window changed with an earlier row.
3. Build the request from the advertised capabilities. Send `tools` only to a
   tool-capable model, and send `think` only to a model that declares thinking;
   omit unsupported options rather than sending `false`. Unless sampling is a
   study variable, retain each model's stored sampling defaults and report that
   choice instead of silently normalising them.
4. Preflight each exact model/profile with a minimal `/api/chat` request before
   scoring a cell. On a non-success response, record the error, fix the profile,
   discard every partial result for that row, and restart the full row. Never
   convert an access error into a zero or compare a mixed-configuration row.
5. Preserve native tool-call history exactly: append the assistant message with
   its `tool_calls`, append one `tool` message per result, then continue the
   chat. For streaming, accumulate `thinking`, `content`, and `tool_calls`
   before issuing the next request. Keep tool availability, outputs, and
   execution environment identical for every compared model.
6. Publish an append-only additional report for a rerun. Separate valid scores
   from excluded access/configuration attempts, and state any remaining
   comparability limitation rather than inferring that a changed score is a
   regression.

The applicable Ollama protocol references are [tool calling](https://docs.ollama.com/capabilities/tool-calling),
[thinking](https://docs.ollama.com/capabilities/thinking), and the
[`/api/chat` request options](https://docs.ollama.com/api/chat).
