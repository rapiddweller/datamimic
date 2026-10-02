# Amendment 58: correct the demo pseudo-initializer description

Date: 2026-09-28.

`resources/demos/__init___.py` has three trailing underscores. It is an ordinary
docstring-only module, not a package initializer. Correct its target sentence
without changing the path or claiming useful runtime ownership. Deletion needs
its own import and packaging check; this amendment changes no behavior or rule.
