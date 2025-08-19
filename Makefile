.PHONY: fmt lint type test unit integration build up down links

fmt:
	ruff check --select I --fix .
	ruff format .

lint:
	ruff check .

type:
	mypy --pretty src

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

# Link checker (Lychee)
LYCHEE_DOCKER=lycheeverse/lychee:latest
LYCHEE_OPTS?=--no-progress --verbose

links:
	docker run --rm --init \
	  -v "$$PWD:/input" \
	  -e GITHUB_TOKEN \
	  $(LYCHEE_DOCKER) $(LYCHEE_OPTS) \
	  /input/docs /input/README.md /input/DESIGN_DOC.md
