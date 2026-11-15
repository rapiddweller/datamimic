# Where CE can support a compliance program

This page moved from the README.

DATAMIMIC provides test-data and execution evidence that can support compliance work. It does not replace your DPO, your CISO, or your auditor. The following are pointers for where DATAMIMIC outputs commonly slot into established programs:

> CE's reproducible, rule-based artefacts are within the tested boundary in the [determinism evidence](https://github.com/rapiddweller/datamimic/blob/development/docs/determinism.md). The DATAMIMIC Enterprise Platform has its own records; the CE matrix does not verify its execution.

| Regulation / standard | Where DATAMIMIC contributes |
|---|---|
| **DORA (Reg. 2022/2554)**, Arts. 24–25, digital operational resilience testing | Reproducible test data can support scenario-based, compatibility, performance, and end-to-end testing |
| **ISO/IEC 27701:2025**, Privacy Information Management System (PIMS) | Synthetic data can reduce PII use in non-production; model and execution evidence can support privacy-management processes |
| **HIPAA Security Rule**, 45 CFR Part 164, Subpart C *(US Covered Entity / Business Associate scope)* | Synthetic healthcare data can reduce the need to copy ePHI into dev/test; safeguards still apply where ePHI exists |
| **GDPR**, Arts. 4(5), 25, 32 | May contribute to a pseudonymisation approach and related privacy-by-design and security measures; whether requirements are met depends on the dataset, additional information, and safeguards |
| **PCI DSS 4.0.1**, Req. 6.5.5 (live PANs not used in pre-production except where the environment is part of the CDE and protected by applicable PCI DSS requirements) | Synthetic card-number test data can reduce the need to use live PANs in pre-production |

> These mappings show where DATAMIMIC can contribute; they are not attestations and do not establish that a dataset or processing activity satisfies the reference.

## Industry message formats

Messages that the DATAMIMIC Enterprise Platform generates in EDIFACT, SWIFT MT or HL7 formats are for test and training environments only. They do not satisfy the SWIFT CSCF v2025 secure-zone controls (1.1 environment protection, 1.4 internet restriction). Do not transmit generated messages from a CSP-attested secure zone.
