Create a repeatable dataset named `depots` with exactly 3 depots, and a second dataset named `slots` with exactly 4 storage slots for each depot, 12 slots in total.

Each depot has a `depot_id`, a whole number that is different for every depot.

Each slot has exactly these three fields:

- `depot_id`, the `depot_id` of the depot that owns the slot;
- `slot_id`, a whole number that is different for every slot in the whole dataset. Make it from the depot's `depot_id` and a counter that only counts the slots inside that one depot;
- `state`, always the text `FREE`.

The counter helps to make `slot_id`, but it is not a field of the slot.

Use seed `56606`.
