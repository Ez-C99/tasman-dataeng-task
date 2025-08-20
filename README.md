# tasman-dataeng-task

## Project Structure

```plaintext
tasman-dataeng-task
├─ .dockerignore
├─ .pre-commit-config.yaml
├─ DESIGN_DOC.md
├─ DEV_LOG.md
├─ LICENSE
├─ Makefile
├─ README.md
├─ src
│  └─ tasman_etl
│     ├─ __init__.py
│     ├─ config.py
│     ├─ db
│     │  ├─ __init__.py
│     │  ├─ engine.py
│     │  ├─ migrations
│     │  │  └─ 001_init.sql
│     │  └─ repository.py
│     ├─ dq
│     │  ├─ __init__.py
│     │  └─ gx
│     ├─ http
│     │  ├─ __init__.py
│     │  ├─ codelists.py
│     │  └─ usajobs.py
│     ├─ logging_setup.py
│     ├─ models.py
│     ├─ runner
│     │  ├─ __init__.py
│     │  └─ run.py
│     ├─ storage
│     │  ├─ __init__.py
│     │  └─ bronze_s3.py
│     └─ transform.py
├─ data
│  ├─ deng_full_response.json
│  └─ sample_get.json
├─ docker
│  ├─ Dockerfile
│  └─ docker-compose.yml
├─ docs
│  ├─ Brief_Insights_and_Requirements.pdf
│  └─ architecture
│     └─ decisions
│        ├─ 0001-runtime-extractor.md
│        ├─ 0002-scheduling.md
│        ├─ 0003-database.md
│        ├─ 0004-data-model-shape.md
│        ├─ 0005-idempotency-key-upsert.md
│        ├─ 0006-secrets-management.md
│        ├─ 0007-api-paging-and-limits.md
│        ├─ 0008-db-security-and-durability.md
│        ├─ 0009-data-quality.md
│        ├─ 0010-integration-testing.md
│        └─ index.md
├─ infra
│  └─ terraform
├─ pyproject.toml
├─ requirements.txt
└─ tests
   ├─ integration
   │  └─ test_upsert.py
   ├─ unit
   │  ├─ test_models.py
   |  └─ test_transform.py
   └─ smoke
      └─ test_dq_smoke.py
```

## Quick Start

```bash
make up                   # starts Postgres
make db-migrate           # applies all SQL migrations
make dq                   # runs the targeted DQ smoke test with visible GE output
make smoke                # runs everything in tests/smoke with -s (no capture)
make test                 # full suite (lint/type/unit/integration) + db-migrate first
```

## Common Terms

"FoDE" = Fundamentals of Data Engineering
