# Amendment 76: expose the DSL time-series result type

Date: 2026-09-29. Decision: root review with Astra advice.

`dsl.api` exports `TimeSeriesConfig`, whose `at()` method returns the existing
`TimeSeriesNamespace` class. Re-export that support type through the same
facade. Its nested model owner and runtime behavior do not change. The root
contract still exposes `dsl.api`, not a new direct implementation path.
