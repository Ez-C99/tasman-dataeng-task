.PHONY: fmt lint type test unit integration build up down links

fmt:
	ruff check --select I --fix .
	black .

lint:
	ruff check .

type:
	mypy app

unit:
	pytest -q tests/unit

integration:
	pytest -q tests/integration

test: lint type unit integration

build:
	docker build -t tasman-etl -f docker/Dockerfile .

up:
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down -v

# Link checker (lychee) – uses Docker
LYCHEE_DOCKER=lycheeverse/lychee:latest
LYCHEE_OPTS?=--no-progress --exclude-mail --verbose
LYCHEE_INPUTS=docs/**/*.md README.md DESIGN_DOC.md
links:
	docker run --rm --init -v "$$(pwd)":/input -e GITHUB_TOKEN $(LYCHEE_DOCKER) $(LYCHEE_OPTS) /input/$(LYCHEE_INPUTS)
