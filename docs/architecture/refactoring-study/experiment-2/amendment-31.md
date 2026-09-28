# Amendment 31: close observed interface omissions

Date: 2026-09-28.

Declare only the IO vocabulary leaves, Domain API types and DSL consumer parser
observed at existing boundaries. Record the document parser's base dependency;
no production code changed. The new Domain API type declarations also
expose generic boundary-analysis UNKNOWNs (`return.service_cls` twice and
`return.age_bands` once); these are analyzer limits, not grounds to hide the
truthful types. Total UNKNOWNs move from 64 to 67 while violations fall 73 to 53.

LOCAL VERIFIED: seven focused architecture tests; fresh ArchKeel scan parsed
494/494 files with no new violation IDs or unused newly declared selectors.
Independent Luna QA and Terra review found no P1/P2. Descriptor inputs remain
930 XML plus seven Intent Models with unchanged hashes.

CI-ONLY VERIFICATION: no remote run. Full validation is still UNKNOWN/exit 2.
