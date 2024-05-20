all: format lint lint_md test

format:
	poetry run ruff format .

lint:
	poetry run ruff check .

lint_md:
	markdownlint "**/*.md" -c .markdownlint.yml

test:
	poetry run pytest -v

test-update-golden:
	poetry run pytest . -v --update-goldens


# source ~/path/to/venv/bin/activate
