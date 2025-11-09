.PHONY: test coverage typecheck lint

test:
	pytest -q

coverage:
	coverage run -m pytest tests/mcp
	coverage report --include="datamimic_ce/mcp/*" --fail-under=90

typecheck:
	mypy --strict datamimic_ce/mcp

lint:
	pylint datamimic_ce/mcp
