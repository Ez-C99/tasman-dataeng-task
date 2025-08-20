# Technical Implementation Document

## Implementation

### 0. Starter Files and Config

**Overview**
Configure the starting state of the repo and setup the environment(s) to support the solution development and packaging.

#### Tasks

- Generate repo structure
- Setup all environment and config files
- Verify the setup works cohesively

#### Acceptance Criteria

- Repo is ready for *smooth* (I hope) development

#### Risks/Trade-offs

- The setup doesn't play well with each other

#### Notes

- The repo structure isn't necessarily set in stone and may need to be changed as I develop the solution
- Because of the boilerplate and lack of actual dev work in this section, most of it can be offloaded to the LLM and I'll double check after
- I've had some Python3.12 issues in the past in general so I need to make sure that the `python:3.12-slim` in my Dockerfile plays nice

**Repo Structure**
The is the starting state of the repo. Based on the extensive design and planning I put in the design doc, I was able to start off with some the basic structure of a `README.md`,  `.gitignore` my design doc and ADRs. From this I could feed them into an LLM to give me a suggested repo structure based on everything I've designed and planned for the project so far

```plaintext
tasman-dataeng-task   
 ┣ src  
 ┃ ┗ tasman_etl  
 ┃ ┃ ┣ db  
 ┃ ┃ ┃ ┣ migrations  
 ┃ ┃ ┃ ┃ ┗ 001_init.sql  
 ┃ ┃ ┃ ┣ __init__.py  
 ┃ ┃ ┃ ┣ engine.py  
 ┃ ┃ ┃ ┗ repository.py  
 ┃ ┃ ┣ dq  
 ┃ ┃ ┃ ┣ gx  
 ┃ ┃ ┃ ┗ __init__.py  
 ┃ ┃ ┣ http  
 ┃ ┃ ┃ ┣ __init__.py  
 ┃ ┃ ┃ ┣ codelists.py  
 ┃ ┃ ┃ ┗ usajobs.py  
 ┃ ┃ ┣ runner  
 ┃ ┃ ┃ ┣ __init__.py  
 ┃ ┃ ┃ ┗ run.py  
 ┃ ┃ ┣ storage  
 ┃ ┃ ┃ ┣ __init__.py  
 ┃ ┃ ┃ ┗ bronze_s3.py  
 ┃ ┃ ┣ __init__.py  
 ┃ ┃ ┣ config.py  
 ┃ ┃ ┣ logging_setup.py  
 ┃ ┃ ┣ models.py  
 ┃ ┃ ┗ transform.py  
 ┣ data  
 ┃ ┣ deng_full_response.json  
 ┃ ┗ sample_get.json  
 ┣ docker  
 ┃ ┣ Dockerfile  
 ┃ ┗ docker-compose.yml  
 ┣ docs  
 ┃ ┣ architecture  
 ┃ ┃ ┗ decisions  
 ┃ ┃ ┃ ┣ 0001-runtime-extractor.md  
 ┃ ┃ ┃ ┣ 0002-scheduling.md  
 ┃ ┃ ┃ ┣ 0003-database.md  
 ┃ ┃ ┃ ┣ 0004-data-model-shape.md  
 ┃ ┃ ┃ ┣ 0005-idempotency-key-upsert.md  
 ┃ ┃ ┃ ┣ 0006-secrets-management.md  
 ┃ ┃ ┃ ┣ 0007-api-paging-and-limits.md  
 ┃ ┃ ┃ ┣ 0008-db-security-and-durability.md  
 ┃ ┃ ┃ ┣ 0009-data-quality.md  
 ┃ ┃ ┃ ┣ 0010-integration-testing.md  
 ┃ ┃ ┃ ┗ index.md  
 ┃ ┗ Brief_Insights_and_Requirements.pdf  
 ┣ infra  
 ┃ ┗ terraform  
 ┣ tests  
 ┃ ┣ integration  
 ┃ ┃ ┗ test_upsert.py  
 ┃ ┗ unit  
 ┃ ┃ ┣ test_models.py  
 ┃ ┃ ┗ test_transform.py  
 ┣ .DS_Store  
 ┣ .dockerignore  
 ┣ .env.example  
 ┣ .gitignore  
 ┣ .pre-commit-config.yaml  
 ┣ DESIGN_DOC.md  
 ┣ DEV_LOG.md  
 ┣ LICENSE  
 ┣ Makefile  
 ┣ README.md  
 ┣ pyproject.toml  
 ┗ requirements.txt
```

#### Starter Files

##### `pyproject.toml`

One file to declare runtime dependencies, dev tooling, and (optionally) build metadata. Uses PEP 621 fields under `[project]`, and a minimal `[build-system]` so it’s wheel-ready if you ever need to package.

- `[project]` is the PEP 621 standard for project metadata; common tools read it.
- `[build-system]` declares how a wheel would be built if you ever publish; `setuptools` is fine and widely supported.
- `black`, `ruff`, `mypy` are configured here so CI and local dev are identical.

> FoDE lens: **Choose common components wisely**; standard packaging keeps things interoperable and easy to reproduce.

Alternatives (LLM-given):

- **Poetry**: lockfile + nice UX if you value a single tool for deps/build/publish. Trade-off: different workflow, lockfile churn in PRs. [python-poetry.org](https://python-poetry.org/docs/?utm_source=chatgpt.com)[GitHub](https://github.com/python-poetry/poetry?utm_source=chatgpt.com)[Real Python](https://realpython.com/dependency-management-python-poetry/?utm_source=chatgpt.com)
- **Hatch**: modern project manager + envs; fast and PEP 621-aligned. Trade-off: new tooling to learn. [hatch.pypa.io+1](https://hatch.pypa.io/?utm_source=chatgpt.com)[Python Packaging](https://packaging.python.org/key_projects/?utm_source=chatgpt.com)
- **pip-tools / uv**: keep your `pyproject.toml`, generate pinned `requirements.txt` deterministically (`pip-compile`) or use **uv** (very fast pip/pip-tools replacement). Trade-off: another command step. [pip-tools.readthedocs.io+1](https://pip-tools.readthedocs.io/?utm_source=chatgpt.com)[astral.sh](https://astral.sh/blog/uv?utm_source=chatgpt.com)

##### `Dockerfile`

Multi-stage build --> slim runtime + non-root user --> safer, smaller image. Healthcheck verifies importability.

- Multi-stage trims the final image and reduces attack surface.
- Non-root (`USER appuser`) is a Docker best practice.

> FoDE lens: Prioritise security (least privilege), Plan for failure (healthcheck).

##### `docker-compose.yml`

Compose spins up Postgres + the ETL; `depends_on` with a **healthcheck** ensures DB is ready before the ETL runs.

- `healthcheck` + `depends_on.condition: service_healthy` gives a predictable startup order.
- Exposes `5432` for psql/GUI clients during development.

> FoDE lens: **Loosely coupled**; each service is replaceable.

Alternatives (LLM-given):

- Good for local. Alternative is a **Dev Container** (VS Code) for fully reproducible dev shells; or skip Compose and run Postgres via **Testcontainers** only in tests. (You’ll already use Testcontainers for integration tests.)

##### `.env.example`

Documented **environment variables** for config. Commit this file; never commit a real `.env`. This follows the 12-Factor **Config** principle.

- Keep secrets out of git; in cloud, use Secrets Manager (later via Terraform).

> FoDE lens: **Reversible decisions**—env-driven config makes swapping services trivial.

Alternatives (LLM-given):

- Perfect for local. In cloud, **Secrets Manager** for real secrets; keep envs orthogonal per 12-Factor (env vars as config).

##### `Makefile`

Fast local ergonomics: **fmt → lint → type → test**; Compose helpers; **link checker** with Lychee (Dockerised). Use `.PHONY` for non-file targets.

- `.PHONY` prevents target/file name collisions.
- Lychee checks links; `GITHUB_TOKEN` avoids GH rate limits.

> FoDE lens: **DataOps**—automation & fast feedback loops.

##### `.pre-commit-config.yaml`

Auto-fix and guardrails on every commit with **pre-commit**. Hooks: **ruff**, **black**, **mypy**.

- Install once: `pre-commit install` → runs on each commit.
- Ruff is a fast “kitchen-sink” linter replacing many plugins; Black is the opinionated formatter; mypy adds static checks.

> FoDE lens: **Software engineering hygiene** → fewer defects, consistent style.

Alternatives (LLM-given):

- Your set is great. Alternatives: add `trailing-whitespace`, `end-of-file-fixer`, and `check-yaml/JSON/TOML` hooks for docs/config hygiene.

#### Sanity Checks and Results

- `pip install -e ".[dev]"`
- `pre-commit install`
- `make up` (starts DB + builds ETL image)
- `make test` (runs linters, types, unit+integration)
- `make links` (docs link check)

The first requirements install failed due to `setuptools` trying to treat my top-level folders (`app`, `data`, `infra`, `docker`) as packages, so it bailed out. The fixes were as below and in [this commit](https://github.com/Ez-C99/tasman-dataeng-task/commit/ca5b6cec60a8ba7a63f2095e8b6869932c139b86):

- Switch to standard `src/` package definition
- Update `pyproject.toml` and pin discovery to `src/` properly
- Fix Python imports and entrypoint in `Dockerfile`
- Upgrade pip and retry the install

More fixes were made in the commit after this to fix `mypy` pathing and the docker `make links` functionality.

#### LLM Prompts

- "Below is my repo so far... Please give me the full repo setup and structure I'll for the rest of the project"
- "Please give me the boilerplate config I'll need in the starter files for development. namely pyproject, Dockerfile, compose, env, Makefile, pre-commit"
- "What are some considerable alternatives to my starter file and why?"
- "Installing requirements isn't working: `{failure log here}`"

### 1. **Bronze Capture (S3)**

**Overview**  
Persist raw USAJOBS responses per page to S3 (`bronze/date=…/run=…/page=N.json`) to enable replay, audits, and schema evolution. (Bronze/Silver/Gold pattern.)

#### Tasks

- Write S3 client (boto3) with S3 SHA-256 checksum verification on upload & `put_object` retry.
- Object keying: `bronze/usajobs/date=YYYY/MM/DD/run={uuid}/page={n}.json`.
- S3 lifecycle: Standard → Glacier Instant Retrieval @30d; expire @180d.

#### Acceptance Criteria

- Every successful API page stored once; idempotent re-runs don’t duplicate (same run_id).
- Lifecycle rules visible in bucket management.

#### Risks/Trade-offs

- Extra storage cost; mitigated by lifecycle.

#### Notes

- The plan is to use a the data-lake patterns of a single S3 bucket with different folders for all the medallion layers (like I have in my workplaces so far in my career).
  - Different buckets is another possible pattern but not necessary for this task

```bash
s3://<env>-tasman-task-usajobs/
  bronze/usajobs/...
  silver/usajobs/...
  gold/usajobs/...
```

- Would be good to later add a remote S3 backend to migrate the state to, so it's not just on my machine, but one thing at a time
- Gzip is good for cutting storage while keeping text-friendly JSON

The S3 object model I want to follow is:
`s3://<bucket>/bronze/usajobs/date=YYYY/MM/DD/run=<UTC_ISO8601_Z>/page=<NNNN>.json.gz`

- `date=...` & `run=...` make each ingest idempotent and listable.
- Multiple prefixes distribute load if/when parallelising later.

The gzipped JSON object body should be as below

```json
{
  "request": {
    "endpoint": "/api/search",
    "params": {"Keyword": "data engineering", "ResultsPerPage": 500, "Page": 1, "LocationName": "Chicago", "Radius": 50},
    "sent_at": "2025-08-19T16:15:30.123Z"
  },
  "response": {
    "status": 200,
    "received_at": "2025-08-19T16:15:31.045Z",
    "headers": {"x-ratelimit-...": "..."},
    "payload": { "LanguageCode": "EN", "SearchResult": {...} }   // full USAJOBS payload
  },
  "ingest": {
    "ingest_run_id": "20250819T161530Z",
    "sha256": "<hex>",
    "bytes_uncompressed": 123456,
    "notes": "raw page 1 of N"
  }
}
```

Storing the full payload means Silver can always be regenerated

Terraform S3 bucket config requirements:

- Block public access
- Encrypted
- Lifecycle should transition after 30 days and delete after 180 (adjustable)

ECS task role needs all the right bucket permissions (put, get, list)

##### DRY and SOLID code

I'm trying to keep the code DRY and SOLID end-to-end, even if it takes longer, so starting here this is the plan

Minimal architecture (interfaces & modules):

- HTTP client (`http/usajobs.py`): a thin wrapper that only knows requests/retries/rate-limit headers. No business logic.
- Bronze writer (`storage/bronze_s3.py`): accepts an envelope dict and writes to S3 (no knowledge of USAJOBS schema).
- Models (`models.py`): Pydantic Data Transfer Objects (DTOs) for parsed records; validators keep parsing rules out of business code.
- Transform (`transform.py`): pure functions from raw JSON --> normalised records; no I/O.
- Repository (`db/repository.py`): SQL/SQLAlchemy upserts; no parsing or HTTP.
- Runner (`runner/run.py`): orchestrates (fetch --> persist raw --> validate --> transform --> upsert), wires dependencies via config.

This separation mirrors SOLID:

- **S**ingle Responsibility: each module does one thing.
- **O**pen/Closed: swap S3 for local FS in tests; swap Postgres for another DB later.
- **L**iskov: design to interfaces (e.g., `StorageWriter`, `Repository`) so mocks/subclasses are drop-ins.
- **I**nterface Segregation: tiny, focused protocols (see example below).
- **D**ependency Inversion: runner depends on abstractions, not concrete boto3/psycopg.

#### LLM Prompts

- "Please generate an IAM task Terraform module for me"
- “Please generate the unit tests for my bronze_s3.py module”
- Fixing the fiddly minutiae of linting in general

### 2. **Schema & Migration (Silver DDL)**

**Overview**  
Create normalised core: `job`, `job_location`, `job_category`, `job_details`, plus `ingest_run`. Use JSONB on `job.raw_json` for safety net; add GIN index. Upserts via `INSERT … ON CONFLICT`.

#### Tasks

- Author `001_init.sql` (foreign keys, primary keys, indexes, simple CHECKs).
- Apply in local Compose and in CI.

#### Acceptance Criteria

- DDL applies cleanly; foreign keys/primary keys enforced; GIN on `raw_json` present.

#### Risks/Trade-offs

- More joins vs. correctness and future evolution.

#### Notes

- **Natural key for idempotency:** `position_id` is the stable announcement code in `MatchedObjectDescriptor`; I'm using a UNIQUE constraint on it and upsert on conflict (atomic insert-or-update), which is the canonical Postgres pattern.
- **Keep lists relational where it matters:** `job_location`, `job_category`, `job_grade` are N:1 child tables so filtering and indexing stay correct (no CSV anti-patterns).
  - This is the product of the improved schema vs the simpler 2 table (1:1) schema I originally thought of
- **Retain the full payload:** `raw_json JSONB` with a GIN index gives “reach-back” and ad-hoc querying without schema churn.
- **Practical datatypes:** use `INTEGER` for pay (whole dollars) and `NUMERIC(9,6)` for latitude/longitude; all timestamps are `TIMESTAMPTZ`.
- **Optional full-text:** a stored **generated column** (`tsvector`) on title+summary is easy to add later; it’s a documented feature and can be GIN-indexed.

Images of the Postgres CLI tables from the following successful command runs will be in the PR for this feature.

```bash
psql "postgresql://postgres:localpw@localhost:5432/usajobs" \
  -f src/tasman_etl/db/migrations/001_init.sql

\dt                         -- expect job, job_details, job_location, job_category, job_grade
\d+ job                     -- confirm columns, uk on position_id, indexes
\di                         -- see trigram/jsonb GIN indexes
```

#### LLM Prompts

- “Please draft the Postgres DDL for job/job_location/job_category/job_details, based on my schema, with sensible types.”
