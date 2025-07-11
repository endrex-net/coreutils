PYTHON_VERSION = 3.12
PROJECT_NAME = coreutils
TEST_FOLDER_NAME = tests

develop: clean-dev ##@Develop Create virtualenv
	python$(PYTHON_VERSION) -m venv .venv
	.venv/bin/pip install -U pip uv
	.venv/bin/uv sync --all-groups --all-extras
	.venv/bin/pre-commit install

local: ##@Develop Run dev containers for test
	docker compose -f docker-compose.dev.yaml up --force-recreate --renew-anon-volumes --build

local-down: ##@Develop Stop dev containers with delete volumes
	docker compose -f docker-compose.dev.yaml down -v

clean-dev: ##@Develop Remove virtualenv
	rm -rf .venv

develop-ci: ##@Develop Create virtualenv for CI
	python -m pip install -U pip uv
	uv sync --all-groups --all-extras

test-ci: ##@Test Run tests with pytest and coverage in CI
	.venv/bin/pytest ./$(TEST_FOLDER_NAME) --cov=./$(PROJECT_NAME)

lint-ci: ruff mypy ##@Linting Run all linters in CI

build-ci: ##@Build Run build in CI
	uv build

ruff: ##@Linting Run ruff
	.venv/bin/ruff check ./$(PROJECT_NAME)

mypy: ##@Linting Run mypy
	.venv/bin/mypy --config-file ./pyproject.toml ./$(PROJECT_NAME)

