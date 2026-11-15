# Pseudonymization with CE

This guide moved from the README. It covers the manual pseudonymization model, converters and key management.

## Pseudonymization (manual model)

DATAMIMIC supports two pseudonymization modes with different repeatability properties:

| Mode | How | Compliance note | Use case |
|---|---|---|---|
| **Seeded** (`rngSeed` set) | Deterministic on the tested profiles | May form part of a pseudonymisation approach. Whether the result qualifies as pseudonymised under GDPR Art. 4(5) depends on whether attribution requires additional information that is kept separately and protected. | Regression testing, stable CI/CD pipelines |
| **Non-seeded** (no `rngSeed`) | Not replay-stable | — | One-time data delivery |

> **Note on GDPR:** Pseudonymisation does not make data anonymous or establish GDPR compliance. Under Recital 26, anonymity depends on whether a person remains identifiable considering means reasonably likely to be used.

In CE, PII fields are identified and modeled manually in the XML pipeline. The source is a
pipe-separated project data file; the scenario `tests_ce/scenarios/s28_pseudonymize_source` runs this model:

```xml
<setup rngSeed="42">
  <generate name="customers" source="data/entity/customers.ent.csv" target="CSV" distribution="ordered">
    <!-- rngSeed makes seeded runs produce the same pseudonyms; remove it for a new
         mapping per run. distribution="ordered" keeps source row N mapped to the
         same pseudonym. -->
    <variable name="p"   entity="Person"      dataset="DE" />
    <variable name="acc" entity="BankAccount" dataset="DE" />

    <key name="customer_id" script="customer_id" />
    <key name="first_name" script="p.given_name" />
    <key name="last_name"  script="p.family_name" />
    <key name="email"      script="p.email" />
    <key name="iban"       script="acc.iban" />
    <key name="birth_date" script="p.birthdate" />
  </generate>
</setup>
```

Built-in converters can additionally transform a key's value — e.g. replace the original
with a keyed hash, or partially mask it. `Hash` derives its HMAC key from `<setup rngSeed>`;
the same input + seed + algorithm + output format + optional salt gives the same token across
runs. Without a seed each run gets a new random key:

```xml
<key name="email" script="p.email" converter="Hash('sha256','hex')" />
<key name="iban"  script="acc.iban" converter="MiddleMask(8, 4)" />
```

For pseudonymization, keep a random key outside the descriptor and separate from the generation
seed. Reference a runtime property in the converter:

```xml
<key name="email" script="p.email"
     converter="Hash('sha256','hex',key=pseudonym_key.encode('utf-8'))" />
```

Supply it from an access-controlled environment variable:

```bash
# Generate once, store securely, and reuse for stable tokens.
export DATAMIMIC_PSEUDONYM_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
datamimic run datamimic.xml --param-env pseudonym_key=DATAMIMIC_PSEUDONYM_KEY
```

`--param NAME=VALUE` and `--param-env NAME=ENV_NAME` are repeatable and override properties
from `conf/environment.env.properties`. Property names must be Python identifiers; duplicate names
are rejected. Use `--param-env` for secrets because command-line values can appear in process
listings and shell history. Runtime properties remain available to descriptor scripts; use trusted
descriptors and control access to the key and source data.

Hash keys must contain at least 32 bytes before adding an optional salt. Length alone does not
prove entropy: use a cryptographic random source, rather than a password, date or generation seed.
Rotating the external key changes tokens for the same input; retain the prior key securely only
when old mappings must be reproduced. An external key keeps tokens stable when `rngSeed` changes
and leaves seeded data generation unchanged. Existing `Hash(...)` calls without an explicit key
retain their seed-derived behavior and its weak-seed limitations.

Available converters (13): `Mask`, `MiddleMask(start, end)`, `CutLength(n)`, `Substring(start, end)`, `JavaHash`, `RemoveNoneOrEmptyElement`,
`Hash(type, format[, salt])`, `DateFormat(fmt)`, `Append`, `UpperCase`,
`LowerCase`, `Date2Timestamp`, `Timestamp2Date`.

```bash
datamimic run ./pseudonymize-customers/datamimic.xml
```

Use a controlled export or staging input. Do not point this workflow at a live production source.

With `rngSeed`: the same descriptor, seed, and ordered source rows reproduce the same replacement sequence; this is not a subject-keyed mapping across reordered exports.

Without `rngSeed`: random/entity replacements use a new run-specific mapping, and hash converters use a new random key; outputs are not replay-stable.
