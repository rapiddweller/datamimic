Create a repeatable dataset named `depots` with exactly 3 depots, and a second dataset named `slots` with exactly 4 storage slots for each depot, 12 slots in total.

Each depot has a `depot_id`: the whole numbers 1, 2 and 3.

Each slot has exactly these three fields:

- `depot_id`, the `depot_id` of the depot that owns the slot;
- `slot_id`, the whole number `depot_id * 100 + n`, where the counter `n` counts only the slots inside that one depot and starts at 1;
- `state`, always the text `FREE`.

The counter helps to make `slot_id`, but it is not a field of the slot.

Use seed `56606`.
