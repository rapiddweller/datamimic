# Amendment 77: retain open property maps

Date: 2026-09-30. Decision: Astra-approved contract correction.

The properties parser accepts arbitrary user keys and splits each line at its
first `=` (`datamimic_ce/engine/dsl/parsers/input/properties.py:21-28`). The IO
reader and connection-profile loader expose that same `dict[str, str]` shape
through public facades. A fixed DTO would reject valid user properties and
misstate the existing API.

Allow only the three exact direct returns in the root contract. Runtime
behavior, API ownership and the open map type remain unchanged. The checker
source is the published `archkeel==0.8.1` release.
