# Amendment 87: exact task Registry ownership

2026-10-02. Decision: Astra. Use published ArchKeel 0.8.4 and assign only
`datamimic_ce.engine.runtime.tasks` to TASKS-REGISTRY through `exact_modules`.

The package initializer imports the Registry to register Statement-to-Task
handlers before dispatch, including cold workers entering below Lifecycle.
Its responsibility was documented, but its executable module had no local owner.
Base owns dispatch mechanics; Registry owns concrete composition. Assigning the
whole Tasks namespace to Registry would wrongly absorb the task families.

Existing selectors, interfaces, requirements and rules stay fixed. No runtime,
descriptor, oracle, baseline or budget changes. Registry's omitted explicit
`public` decision remains a separate target-definition gap, not cleared here.
Step 88 records published-checker before/after evidence and remaining uncertainty.
