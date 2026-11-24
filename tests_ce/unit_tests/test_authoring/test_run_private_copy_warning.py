"""`authoring run --allow-side-effects` writes files into a private copy. The result must say so."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import RunRequest

_XML = (
    '<setup><generate name="rows" count="2" target="CSV">'
    '<key name="n" generator="IncrementGenerator"/></generate></setup>'
)


@pytest.mark.parametrize(("allow", "warned"), [(True, True), (False, False)])
def test_run_warns_that_files_stay_in_a_private_copy_only_when_side_effects_are_allowed(tmp_path: Path, allow, warned):
    result = create_authoring_application(workspace_root=tmp_path).run(RunRequest(xml=_XML, allow_side_effects=allow))
    assert result.ok
    messages = [item.message for item in result.diagnostics if item.severity == "warning"]
    assert any("private copy" in message for message in messages) is warned
