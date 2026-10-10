# Amendment 25: publish actual Source and target operations

Date: 2026-09-28. Astra decision before the IO source split.

Publish the two already-used IO source-entity helpers and the target-routing
operations from their owners. Move Mongo upsert-target classification to IO
exporter routing; Runtime calls it only at its existing conditional points.
Remove that operation and the neutral nested-key row window from the Runtime
source API; callers use their IO owners directly. Source adapters do not use
the task base component, so remove that unused dependency.

No wrapper, new contract scope or broader dependency permission is added.
Neutral row-window functions remain in `io/contracts.py` under Amendment 21.
