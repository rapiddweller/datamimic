# Amendment 59: declare Generate's source-kind token

Date: 2026-09-28.

Moving Generate file-source classification from Runtime to IO makes the IO
router use the existing DSL `EL_GENERATE` token. Declare that token at the DSL
interface. This adds no dependency direction: IO already requires DSL vocabulary.
The initial candidate report caught the undeclared import as `INTERFACES-ONLY`.
Reader selection and file windows move to IO; expression evaluation stays in
Runtime. Descriptor behavior must remain unchanged.
