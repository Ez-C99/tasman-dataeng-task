.PHONY: fmt lint type unit integration test build up down links db-migrate

fmt:
	ruff check --select I --fix .
	ruff format .

lint:
	ruff check .

type:
	mypy --pretty src

unit:
	python -m pytest -q tests/unit

integration: db-migrate
	python -m pytest -q tests/integration

# Single source of truth: run everything, and ensure schema is applied first.
test: db-migrate lint type unit integration

build:
	docker build -t tasman-etl -f docker/Dockerfile .

up:
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down -v

# Link checker (Lychee)
LYCHEE_DOCKER ?= lycheeverse/lychee:latest
LYCHEE_OPTS   ?= --no-progress --verbose --root-dir /input

links:
	docker run --rm --init \
	  -v "$$PWD:/input" \
	  -e GITHUB_TOKEN \
	  $(LYCHEE_DOCKER) $(LYCHEE_OPTS) \
	  /input/docs /input/README.md /input/DESIGN_DOC.md


# Postgres migrations
PSQL_URL  ?= postgresql://postgres:localpw@localhost:5432/usajobs
MIGRATIONS := $(shell ls -1 src/tasman_etl/db/migrations/*.sql 2>/dev/null | sort)

db-migrate:
	@if [ -z "$(MIGRATIONS)" ]; then \
		echo "No migrations to apply"; \
	else \
		for f in $(MIGRATIONS); do \
			echo ">> $$f"; \
			psql "$(PSQL_URL)" -v ON_ERROR_STOP=1 -f "$$f"; \
		done; \
	fi
