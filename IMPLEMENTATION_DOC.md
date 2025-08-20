# Technical Implementation Document

## Implementation

### General Overview

- I tend to leave more comments in my code than the strategy I’ve taken with this project but it’s for a reason.
  - Considering the extensive breakdown and thought process covered by the design doc, this doc and the docstrings, module summaries, branches and PRs throughout, I don’t think all this code **NEEDS** so many comments for the sake of commenting
  - I’m already trying to provide enough documentation, in and out of the code, to tell the story so I don’t want to add too much bloat to what you read

---

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

---

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

---

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

---

### 3. **Validation Models (Pydantic v2)**

**Overview**  
Define strict-enough Pydantic models for USAJOBS responses and normalised records. Goals: (1) coerce messy strings to clean types, (2) reject impossible values early, (3) produce DTOs that map 1:1 to Silver tables.

#### Tasks

- Model the USAJOBS raw response (only used fields; ignore the rest).
- Add validators for:
  - Pay min/max (strings → `int`, ensure `min <= max`).
  - Booleans arriving as “Yes/No” → `bool`.
  - Dates → `datetime` (UTC assumed).
- Provide normalised DTOs: `JobRecord`, `JobDetailsRecord`, `JobLocationRecord`, `JobCategoryRecord`, `JobGradeRecord`.
- A helper to parse an entire page (`model_validate_json`) and yield normalised records.

#### Acceptance Criteria

- Parsing a real page yields:
  - All `JobRecord` fields typed (ints, bools, datetimes).
  - Lists handled (locations/categories/grades).
  - Invariants enforced (e.g., `pay_min <= pay_max`).
- Unit test covers a happy-path item and a couple of edge cleanups (e.g., “Yes” → `True`).

#### Risks/Trade-offs

- Making the models too strict can break on minor upstream drift. I should keep strictness per-field where it matters (pay/date/booleans) and allow extra fields to be ignored for forward compatibility.

#### Notes

Pydantic v2 features as opposed to v1:

- `model_validate(_json)` is the canonical v2 entrypoint; `model_dump()` for safe dicts.
- `@field_validator` replaces v1 `@validator` and supports before/after modes for coercion vs. checks.
- `computed_field` lets you surface `details` from `UserArea` without bloating the stored model.
- I'm intentionally keep model config lax by default (ignore unknowns) but apply strictness to critical fields; that’s “strict mode where it matters.”

> FoDE lens:
>
> - Plan for failure: validate at boundaries; fail fast.
> - Loosely coupled & evolvable: ignore unknown fields; keep `raw_json` stored in Silver for “reach-back.”
> - Software hygiene: clear separation—parsing in models, I/O elsewhere.

How this module will (hopefully) seamlessly fit into the bigger picture:

- Runner* calls `parse_page_json(...)` on the USAJOBS response body, then `normalise_item(...)` per item.
- The returned DTOs map *directly* to Silver upsert SQL you have ready.
- This keeps concerns clean: HTTP fetch -> Bronze write -> Validate/normalise (here) -> Silver upsert.

#### LLM Prompts

- “Please give me a function to normalise my API items into data transfer objects”
- "Please generate my unit tests for models.py using the following test payload as inspiration"

```python
    # Minimal synthetic payload mimicking USAJOBS
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "123",
                    "MatchedObjectDescriptor": {
                        "PositionID": "ABCD-1234",
                        "PositionTitle": "Data Engineer",
                        "PositionURI": "https://www.usajobs.gov/job/123",
                        "ApplyURI": ["https://apply.example/apply"],
                        "PositionLocationDisplay": "Chicago, IL",
                        "PositionLocation": [
                            {"LocationName": "Chicago, Illinois, United States",
                             "CountryCode": "US", "CountrySubDivisionCode": "IL",
                             "CityName": "Chicago", "Longitude": -87.6298, "Latitude": 41.8781}
                        ],
                        "OrganizationName": "Some Agency",
                        "DepartmentName": "Dept",
                        "JobCategory": [{"Name": "IT Mgmt", "Code": "2210"}],
                        "JobGrade": [{"Code": "GS-13"}],
                        "QualificationSummary": "Do data stuff.",
                        "PositionRemuneration": [{"MinimumRange": "$95,000", "MaximumRange": "120,000", "RateIntervalCode": "PA"}],
                        "PublicationStartDate": "2025-08-01T00:00:00Z",
                        "ApplicationCloseDate": "2025-08-31T23:59:59Z",
                        "UserArea": {
                            "Details": {
                                "JobSummary": "Summary",
                                "DrugTestRequired": "Yes",
                                "TeleworkEligible": True,
                                "RemoteIndicator": False,
                                "MajorDuties": ["A", "B"]
                            }
                        }
                    }
                }
            ]
        }
    }

```

---

### 4. **Transformation (Normalise to Silver)**

**Overview**  
Explode multi-valued fields (`PositionLocation`, `JobCategory`) into child rows; map codelists to human-readable labels. Keep arrays (e.g., `HiringPath`) in JSONB initially; index later if needed.

#### Tasks

- Pure functions in `transform.py` from parsed model → `{job, locations, categories, details}` dicts.
- Add codelist client & cache.

#### Acceptance Criteria

- Given a recorded sample page, produce deterministic row sets.

#### Risks/Trade-offs

- Slight complexity vs. queryability.

#### Notes

- USAJOBS exposes Codelist endpoints (no auth) for things like schedule types and you can fetch them to map codes to human-readable labels during transform
- Their developer docs describe both the search response shape (e.g., `SearchResultItems` and `MatchedObjectDescriptor`) and the codelists and how to call them.

##### `src/tasman_etl/http/codelists.py`

A small client with in-memory TTL cache

##### `src/tasman_etl/transform.py`

Pure functions that:

- iterate the parsed page,
- use your existing Pydantic DTOs (`normalise_item` from `models.py`),
- (optionally) enrich a couple of coded fields via `CodelistClient`,
- return row dicts ready for loading.

You'll see that I declared the 'Bundle' class with a dataclass decorator of the parameter `(frozen=True)`. This means:

- You can’t reassign fields after you create the object (trying raises an error)
- Only the attribute names are locked; if a field holds a list/dict, its contents can still change.
- Safe to use as a dict key or in a set (hashable by default).
- Use immutable types (e.g. tuple) to not change inner data.

This is a practice I'll maintain throughout throughout the scripts wherever necessary, for the following reasons:

- Avoids accidental mutation; objects stay stable after creation.
- Simplifies reasoning, testing, and debugging (pure transforms).
- Enables safe reuse: hashable for sets/deduplication/cache.
- Improves data integrity for ETL, idempotent upserts, and DQ checks.
- Lowers concurrency & side‑effect risks (read‑only objects).
- Clear audit trail: raw + derived fields can’t drift pre‑load.
- Easier refactors (value-object semantics).
- Facilitates deterministic change detection and memoisation. (store results without same computations many times)
- Encourages immutable inner types where needed for full safety.

##### How this fits the SOLID/DRY plan

- **Pure transforms**: no I/O or DB knowledge in `transform.py`.
- **Separation of concerns**: `http.codelists` only knows how to fetch & cache code lists (and is optional).
- **Stable DTO boundary**: you already validate and coerce with Pydantic; the loader will consume these dicts next.

#### LLM Prompts

- “Please generate the transform tests based on the module”

---

### 5. **Loader (Idempotent Upserts)**

**Overview**  
Batch UPSERT into `job` (natural key `MatchedObjectId`), then `job_location`, `job_category`, `job_details`. Use short transactions and `statement_timeout`.

#### Tasks

- Parameterised SQL with `ON CONFLICT DO UPDATE` for each table.
- Per-page transaction; per-page metrics.

#### Acceptance Criteria

- Re-running a page yields zero duplicates; updates touch `updated_at`.

#### Risks/Trade-offs

- Wider `DO UPDATE` may stamp newer fields; keep columns minimal until needed.

#### Notes

- Use `INSERT ... ON CONFLICT DO UPDATE` for atomic upserts; this is the canonical PostgreSQL pattern.
- Wrap the per-page load in a single transaction and set a short `statement_timeout` so a slow query can’t stall the run.
- Send `raw_json` as a JSON value (not a string) via `psycopg.types.json.Json`.

In my struggles to get the first integration test working, this is what I found:

- **Timeout semantics**: Set a short per-txn timeout via `SET LOCAL statement_timeout = '5s'`. Postgres expects unit-suffixed values as strings; parameter binding isn’t valid for server GUCs.
- **Upsert pattern**: Use `INSERT … ON CONFLICT DO UPDATE` on `job(position_id)` and child unique keys for atomic idempotency; this is the recommended approach in Postgres for upsert behaviour.
- **JSONB writes**: Send `raw_json` using `psycopg.types.json.Json(...)` to ensure proper JSON typing into `jsonb`.
- **Migrations first**: `integration`/`test` targets now depend on `db-migrate` to remove DDL drift.
- **Make hygiene**: Consolidated `test` to avoid overriding recipes for the same target (GNU Make keeps the last recipe).

#### LLM Prompts

- “Please write the SQLAlchemy/psycopg upsert for job with ON CONFLICT and updated_at=now().”
- "Please give me a quick integration test using `psycopg`"

### 6. **Great Expectations (Pre-load Gate)**

**Overview**  
Small suite: non-nulls on keys, pay range sanity, URL regex, date ordering, ≥1 location per job. Generates Data Docs for review.

#### Tasks

- Build context in `app/tasman_etl/dq/gx/`; checkpoint before DB write (or right after staging).
- Wire into `runner`.

#### Acceptance Criteria

- Suite passes locally & in CI; failure blocks load and logs summary.

#### Risks/Trade-offs

- Keep expectations lean to avoid test brittleness.

#### Notes

- Started with a normal plug-n-play gx system that I normally follow for a suite but I was lead down a great learning path of the library when trying to tailor my solution to the wider context of this project. I'll have the LLM generate a summary of my findings below

##### GX public API vs direct factory import (LLM generated)

Pros of public API (import great_expectations as gx; context = gx.get_context()):

- Stability: gx.get_context() is the documented, supported entry point; internal module paths can shift in minor releases.
- Upgrade resilience: Less likely to break when you bump great-expectations (esp. 0.18 → 0.19+ changes).
- Maintainability: New contributors instantly recognise the pattern from docs.
- Deprecation signalling: Public API surfaces warnings earlier; internal imports may bypass helper shims.
- Easier abstraction: You can wrap gx.get_context() in your own helper for caching/injection in tests.
- Future modes: Supports keyword args (e.g. mode="ephemeral") without chasing factory signatures.

Cons of public API:

- Slightly broader import (top-level package) versus a targeted function; negligible in practice.
- Type specificity: Direct factory import sometimes provides clearer types to static analyzers (minor; you can add a cast).

Pros of current direct factory import:

- Explicit: Signals exactly which internal function is used.
- Marginally minimal import path (very small practical gain).
- May keep mypy from needing a cast if stubs align (depends on version).

Cons of current approach:

- Relies on internal layout (great_expectations.data_context.data_context.context_factory) that can refactor.
- Harder for others to map to documentation (cognitive overhead).
- Risk of silent breakage on library upgrade in a scheduled ECS task (failure mid-run; wastes invocation).

ECS / scheduled EventBridge context:

- Cold start cost: Both approaches pay similar import cost; no material performance difference.
- Resilience matters more: Scheduled jobs should fail only for real data issues, not library internals moving.
- Container image longevity: You may upgrade GE less frequently; using public API minimises dormant fragility.
- Simplified observability: Log messages + warnings are aligned with documented entry points (easier triage).

Recommendation:
Switch to the public API. Wrap it once so you can cache and mock:
import great_expectations as gx
_context = None
def get_gx_context():
    global _context
    if_context is None:
        _context = gx.get_context()  # optionally mode=\"ephemeral\"
    return _context

Then call get_gx_context() inside validate_page_jobs. This gives:

- Single place to tweak modes or config directories.
- Optional caching to avoid repeated initialisation if you validate multiple pages in one run.
- Clean seam for tests (monkeypatch get_gx_context).

_optional tweak to *has_locations (if desired)*:
def_has_locations(rows):
    return next(iter(rows), None) is not None

But leaving it as-is is fine since you pass a list.

Summary: Adopt gx.get_context() via a small wrapper for future-proofing and testability; negligible downside for your ECS workload.

##### `len(list({list_input}))` vs `next(iter({list_input}))` (LLM generated)

Difference when loc_rows is already a list:

- Current code: len(list(loc_rows)) >= 1
  - list(loc_rows) creates a new list copy (O(n) time, O(n) extra memory).
  - len(...) then checks size. Wasteful duplication.
- Lazy check: next(iter(loc_rows), None) is not None
  - Creates an iterator (O(1)) and fetches one element (O(1)).
  - No copying; constant extra memory.

Why “perfectly lazy”:

- For a generic iterable (could be a generator), next(iter(...), None) stops after the first element—doesn’t traverse or realise the rest.
- list(...) forces full materialisation: triggers all iteration side effects, loads everything into memory.

Caveats:

- If loc_rows could be a one-shot iterator you still need that first element later, next() would consume it (you’d lose it). With a list that’s not an issue (lists aren’t consumed).
- If you always receive a list, simplest is just: return len(loc_rows) > 0 or return bool(loc_rows).

Summary:

- For a list: prefer bool(loc_rows) (fastest, no copy).
- For arbitrary iterable you don’t need to preserve: next(iter(x), None) is not None (lazy).
- Avoid len(list(x))—it’s the most expensive form.

#### LLM Prompts

- “What's wrong with my suite?” - fix linting errors
- "What are the pros and cons of importing the context as the public API versus the approach I've taken here"
- "What's missing in my transition to the public API?" - trying to avoid linter suppressors and import properly, accounting for edge cases
- "Computationally, what is the difference between `len(list(loc_rows)) >= 1` and `next(iter(loc_rows), None) is not None` when loc_rows is a list? Also, why is it perfectly lazy to use the latter?"
