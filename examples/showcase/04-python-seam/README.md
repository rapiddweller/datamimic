# How do I extend the DSL with custom python generators and converters?

Write plain python classes and load them with `<execute uri="script/components.scr.py"/>`.
After that they are addressable like built-ins:

- `MaskedPanGenerator(BaseLiteralGenerator)` with a `generate()` method
  becomes `generator="MaskedPanGenerator()"`.
- `RiskBucketConverter(Converter)` with a `convert(value)` method becomes
  `converter="RiskBucketConverter()"` and transforms the field it sits on.

The third integration level is no integration at all: `analyze.py` is a plain
python script that post-processes the generated JSON. Reporting, aggregation,
and validation are ordinary code; the DSL does not trap you.

## Run it

```bash
datamimic run examples/showcase/04-python-seam/datamimic.xml
python examples/showcase/04-python-seam/analyze.py
```

## Where the seam sits

| Concern | Tool |
|---|---|
| Structure, counts, relationships, reproducibility | DSL |
| One field with domain logic (masked PAN, risk bucket) | a small custom class |
| Per-record expressions | `script=` inline python |
| Reporting over the output | plain python script |

## Semantic rules this example demonstrates

- `<execute uri="*.py">` loads classes into the descriptor context; no
  registration, no plugin packaging, no entry points.
- `converter=` chains with `;` and takes constructor syntax:
  `converter="CutLength(10); Append('_test')"`.
- A key with `script="limit_eur" converter="RiskBucketConverter()"` derives
  one field from another and transforms it in one line.

## What the same thing costs in hand-written code

Nothing here is hard in python. The point is the seam: 8 lines of python where
python is right, and zero python for the structure, counts, foreign keys, and
seeding around it.
