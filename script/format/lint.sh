#!/bin/sh

# Print commands and their arguments as they are executed.
# http://linuxcommand.org/lc3_man_pages/seth.html
set -x

# http://mypy-lang.org/
mypy datamimic_ce

ruff check datamimic_ce
