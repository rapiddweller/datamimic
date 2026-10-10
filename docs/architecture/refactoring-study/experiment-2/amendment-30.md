# Amendment 30: scope completeness rules to their owners

Date: 2026-09-28.

Assignment rules now scan the model, parser, task, and generate package trees
their mounted components actually own. The task/client prohibition covers all
runtime task modules, not just the task registry. No production code changed.

LOCAL VERIFIED: recursive definition check and five architecture tests pass;
candidate report 76 → 73 violations with no new findings. Independent Terra
review challenged the task import guard; exact-package and similarly named
negative fixtures now cover its matcher.

CI-ONLY VERIFICATION: no remote run. The full contract still reports UNKNOWN.
