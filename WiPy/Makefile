init:
		poetry install

test:

		poetry run pytest tests
		poetry run black --check --diff pyric/ tests/

format:
		poetry run black pyric/ tests/