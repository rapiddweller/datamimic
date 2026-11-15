# Security policy

## Supported versions

Security corrections go into the latest release of DATAMIMIC Community Edition on PyPI and into the `development` branch.

## Report a vulnerability

Do not open a public issue for a vulnerability.
Use [GitHub private vulnerability reporting](https://github.com/rapiddweller/datamimic/security/advisories/new).
Give the CE version, the steps to reproduce the problem, and the effect.
We confirm that we received the report within 5 working days.

## Scope

CE runs models and scripts that you give it. A model can contain Python expressions and can write to the targets that it names. Run only models that you trust. This is the design, not a vulnerability.
