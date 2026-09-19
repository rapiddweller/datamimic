# DATAMIMIC Enterprise Platform

DATAMIMIC is the test data platform for regulated banking and insurance. It generates
deterministic, reproducible, CI/CD-ready test data. The Enterprise Platform's template
engine additionally produces SWIFT MT, EDIFACT, and HL7 messages for test and training
environments, without production data ever leaving your environment.

The Community Edition provides the runnable execution core. The Enterprise Platform adds
the governed workflow around it: source-informed model creation, human review, operational
controls, and coordinated execution across systems.

## Governed test-data operations

### Reviewable model creation

The Platform reads source data and models relational structure so that generated data can
preserve the relationships required by the target system. PII-relevant fields are surfaced
through risk scoring and recommendations. A user reviews, overrides, or explicitly defines
the decision; the human decision is recorded rather than silently inferred.

### Operational controls

The Platform adds role-based access, scheduling, audit-trail views, reusable templates, and
multi-system execution workflows. Models remain human-readable engineering artifacts: they
show what is generated or transformed at field level, while run records provide the
operational evidence for what was executed.

## Deterministic rules and optional ML generation

Rules-based generation is the default for test cases that need reproducibility, explicit
business logic, and reviewable constraints. With the same engine version, model, and seed,
the deterministic engine produces byte-identical output across machines and over time.

For distributional realism in analytics or training scenarios, the Platform also provides
auto-regressive ML generation. This mode models learned distributions; it is not a
byte-identical replacement for rules-based generation and does not make output anonymous by
default.

## De-identification with clear boundaries

Deterministic, linkable transformations are pseudonymization, not anonymization. The same
input value can map consistently across topics, which preserves referential integrity but
means the result remains personal data. An anonymization claim requires record-level handling
of quasi-identifiers and a re-identification assessment.

The Platform supports risk-based PII recommendations with human confirmation and override.
It does not rely on silent, fully automatic PII classification.

## Message templates for test and training

The Enterprise Platform template engine provides SWIFT MT, EDIFACT, and HL7 message
generation for test and training environments. These outputs are not network-validated and
must not be transmitted on production SWIFTNet or EDI networks. ISO 20022 and other vertical
dialects are implemented per customer engagement on the same template framework rather than
being presented as a guaranteed stock catalogue.

## Learn more

- [DATAMIMIC documentation](https://docs.datamimic.io/)
- [Enterprise Platform](https://datamimic.io)
- [Contact the DATAMIMIC team](https://datamimic.io/contact)
