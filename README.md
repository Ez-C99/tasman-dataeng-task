# Ezra Chamba Tasman Data Engineering Task — USAJOBS ETL

End-to-end pipeline that pulls jobs from the USAJOBS API, persists raw pages to **S3 Bronze**, validates the data with **Great Expectations**, normalises to DTOs, and **upserts** into **Postgres**. Designed for local dev with Docker/Make, and cloud scheduling with **EventBridge → ECS RunTask** (Terraform).

---

## ✨ Features

* **Bronze capture (S3):** gzipped JSON, deterministic bytes, SHA-256 metadata.
* **Data Quality gate (Great Expectations):** URL regex, non-nulls, pay range sanity, “≥1 location” guard.
* **Idempotent loader (Postgres):** `INSERT … ON CONFLICT DO UPDATE` on natural key.
* **Orchestration:** `ingest_search_page()` wires HTTP → Bronze → GX → Transform → Load.
* **Infra-as-code:** ECS + ECR + EventBridge + IAM + CloudWatch Logs (Terraform, eu-west-2).
* **Developer ergonomics:** Makefile targets, Ruff/Mypy, unit + integration + smoke tests.

---

## 📚 Project Docs (read this first)

These three docs are the backbone of the solution. They explain *why* each design choice was made, *how* the system evolved, and *what* was implemented—so reviewers can follow the journey, not just the code.

* **Task Brief — annotated requirements (Goodnotes)**  
  👉 [docs/Brief_Insights_and_Requirements.pdf](docs/Brief_Insights_and_Requirements.pdf)  
  The original task brief marked up by hand with notes. Captures the problem framing, constraints, and early insights that shaped priorities, acceptance criteria, and scope

* **Design Doc — the “why” & architecture**  
  👉 [DESIGN_DOC.md](DESIGN_DOC.md)  
  Scope, constraints, target personas, and end-to-end architecture. Includes trade-offs, data model rationale, paging/rate-limits, medallion layers, and scheduling strategy. Use this to understand the north star before diving into code.  
  Related: Architectural Decision Records (ADRs) in [`docs/architecture/decisions/`](docs/architecture/decisions/index.md).

* **Implementation Doc — the “how” & what shipped**  
  👉 [IMPLEMENTATION_DOC.md](IMPLEMENTATION_DOC.md)  
  Feature-grouped narrative from Bronze → Transform → Loader → DQ → Scheduling. Each section lists tasks, acceptance criteria, risks/trade-offs, and notes. It ties commits/PRs to the plan and calls out important deltas and gotchas encountered during build.

* **Dev Log — the daily story & context**  
  👉 [DEV_LOG.md](DEV_LOG.md)  
  A chronological diary capturing decisions, detours, and timeboxing. This is helpful for interviewers and maintainers to see priorities, pressure points, and how the approach adapted under constraints.

**How to review (suggested flow):**

1) Skim the **Design Doc** for intent and architecture.  
2) Read the **Implementation Doc** sections 1–7 to see how the intent became code.  
3) Scan the **Dev Log** to understand sequencing and trade-off timing.  
4) Jump back here to acquaint youself with and run the project locally or deploy to ECS.

---

## 🗺️ Repo at a glance

```plaintext
tasman-dataeng-task
├─ .dockerignore
├─ .pre-commit-config.yaml
├─ DESIGN_DOC.md
├─ DEV_LOG.md
├─ IMPLEMENTATION_DOC.md
├─ LICENSE
├─ Makefile
├─ README.md
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
│     ├─ .terraform.lock.hcl
│     ├─ iam_task.tf
│     ├─ main.tf
│     ├─ outputs.tf
│     ├─ providers.tf
│     ├─ s3_bronze.tf
│     ├─ secrets.tf
│     └─ variables.tf
├─ pyproject.toml
├─ scripts
├─ src
│  └─ tasman_etl
│     ├─ __init__.py
│     ├─ config.py
│     ├─ db
│     │  ├─ __init__.py
│     │  ├─ engine.py
│     │  ├─ migrations
│     │  │  ├─ 001_init.sql
│     │  │  └─ 002_child_timestamps.sql
│     │  └─ repository.py
│     ├─ dq
│     │  ├─ __init__.py
│     │  └─ gx
│     │     └─ validate.py
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
└─ tests
   ├─ conftest.py
   ├─ integration
   │  ├─ test_run_ingest_integration.py
   │  └─ test_upsert.py
   ├─ smoke
   │  └─ test_dq_smoke.py
   └─ unit
      ├─ test_bronze_s3.py
      ├─ test_models.py
      ├─ test_run_ingest.py
      ├─ test_transform.py
      └─ test_validate.py

```

---

## ⚙️ Prerequisites

* **Python 3.12**
* **Docker** (and `docker compose`)
* **Postgres** (local via compose)
* **AWS CLI v2** (for ECR/ECS/Logs), an AWS account, and a profile (e.g. `tasman-dev`)
* (For cloud) **Terraform** ≥ 1.6

---

## 🔐 Configuration

Create a local `.env` (example below). In cloud, secrets are pulled from **AWS Secrets Manager**.

```env
# USAJOBS API
USAJOBS_USER_AGENT=your-registered-email@example.com
USAJOBS_AUTH_KEY=xxxxxxxxxxxxxxxxxxxx

# Bronze S3 (local runs may stub this; ECS requires real bucket)
BRONZE_S3_BUCKET=dev-tasman-task-usajobs
BRONZE_S3_PREFIX=bronze/usajobs

# Postgres
DB_URL=postgresql://postgres:localpw@localhost:5432/usajobs

# DQ gate
DQ_ENFORCE=true

# Default search params (used by orchestration)
KEYWORD=data
LOCATION_NAME=Chicago
MAX_PAGES=1
```

> In ECS, **Secrets Manager** names are configurable via Terraform variables:
>
> * `usajobs_auth_secret_name` (default `tasman/dev/usajobs/auth`)
> * `db_url_secret_name` (default `tasman/dev/db/url`)

---

## ▶️ Local development

### Install & tooling

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### Start services & run tests

```bash
# Start Postgres (and optional local etl container)
make up

# Apply DB migrations (idempotent)
make db-migrate

# Lint, type-check, and tests (unit + integration)
make test

# DQ / GX smoke suite with visible output
make dq        # or: make smoke

# Shutdown
make down
```

### One-off ETL run (local Python)

```bash
python -c "from tasman_etl.runner.run import ingest_search_page; \
print(ingest_search_page(run_id='local-test', page=1, keyword='data', location_name='Chicago, Illinois', radius_miles=None))"
```

---

## 🧪 Data Quality (GE)

* Uses **Great Expectations** against a pandas DataFrame constructed from DTOs.
* Expectations include:

  * `position_id` / `position_title` non-nulls
  * `position_uri` matches `^https?://`
  * `pay_min` / `pay_max` ≥ 0
  * `pay_min` ≤ `pay_max`
  * Python-side “at least one location” per page
* **Note:** current implementation targets **pandas < 2.0** (see `pyproject.toml` pin).

Run the smoke test:

```bash
make dq
# or
pytest -s tests/smoke/test_dq_smoke.py
```

---

## 🗃️ Database (Silver)

Apply DDL:

```bash
psql "$DB_URL" -f src/tasman_etl/db/migrations/001_init.sql
```

Tables:

* `job(position_id unique, …, raw_json jsonb)`
* `job_location(job_id, loc_idx unique per job)`
* `job_category(job_id, code unique per job)`
* `job_grade(job_id, code unique per job)`
* `job_details(job_id unique)`

Upserts are idempotent (`ON CONFLICT … DO UPDATE`). `raw_json` is stored as JSONB for reach-back.

---

## 🪣 Bronze layout (S3)

```bash
s3://<bucket>/<prefix>/date=YYYY/MM/DD/run=<run_id>/page=NNNN.json.gz
```

* **Deterministic gzip** (mtime=0) and SHA-256 checksum stored in object metadata.
* Bronze envelope contains `request`, `response` (headers + payload), and `ingest` metadata.

---

## ☁️ Cloud deployment (ECS + EventBridge)

> Region assumed: **eu-west-2**. Adjust variables as needed.

### 1) Provision with Terraform

```bash
cd infra/terraform
terraform init -upgrade

# Provide your USAJOBS user agent on first apply
terraform apply \
  -var="aws_profile=tasman-dev" \
  -var="aws_region=eu-west-2" \
  -var="usajobs_user_agent=your-registered-email@example.com"
```

**Important TF variables (selection):**

* `usajobs_auth_secret_name` (or set `usajobs_auth_key` to have TF create one in dev)
* `db_url_secret_name` (preferred) or `db_url` (dev only)
* `schedule_expression` (default daily: `cron(0 0 * * ? *)`)
* `keyword`, `location_name`, `max_pages`
* `container_cpu`, `container_memory`

Outputs include:

* `ecr_repo_url`
* `ecs_cluster_arn`
* `task_definition_arn`
* `event_rule_name`
* `log_group`

### 2) Build & push image to ECR

```bash
export AWS_REGION=eu-west-2
export AWS_PROFILE=tasman-dev
REPO_URL=$(terraform -chdir=infra/terraform output -raw ecr_repo_url)
REGISTRY="${REPO_URL%%/*}"

aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" \
  | docker login --username AWS --password-stdin "$REGISTRY"

GIT_SHA=$(git rev-parse --short HEAD)
docker buildx build --platform linux/amd64 -t etl-temp:latest -f docker/Dockerfile --load .
docker tag etl-temp:latest "${REPO_URL}:latest"
docker tag etl-temp:latest "${REPO_URL}:${GIT_SHA}"
docker push "${REPO_URL}:latest"
docker push "${REPO_URL}:${GIT_SHA}"
```

> **Tip:** Prefer immutable tags (`:${GIT_SHA}`) and update the task definition to pin that digest for reproducible deploys. With `:latest`, consider re-registering the task definition on changes.

### 3) Trigger a manual run & tail logs

```bash
CLUSTER_ARN=$(terraform -chdir=infra/terraform output -raw ecs_cluster_arn)
LATEST_TD=$(terraform -chdir=infra/terraform output -raw task_definition_arn)

aws ecs run-task \
  --cluster "$CLUSTER_ARN" \
  --launch-type FARGATE \
  --task-definition "$LATEST_TD" \
  --network-configuration "awsvpcConfiguration={subnets=$(aws ec2 describe-subnets --filters Name=default-for-az,Values=true --query 'Subnets[0].SubnetId' --output text --region $AWS_REGION),assignPublicIp=ENABLED,securityGroups=$(aws ec2 describe-security-groups --filters Name=group-name,Values=$(basename $(terraform -chdir=infra/terraform output -raw ecs_cluster_arn) | sed 's/-cluster/-etl-sg/'))}" \
  --region "$AWS_REGION" --profile "$AWS_PROFILE"

# Logs
LOG_GROUP=$(terraform -chdir=infra/terraform output -raw log_group)
aws logs tail "$LOG_GROUP" --follow --region "$AWS_REGION" --profile "$AWS_PROFILE"
```

EventBridge will invoke the same **RunTask** on the configured schedule (UTC).

---

## 🧰 Make targets (quick reference)

```bash
make fmt           # Ruff import order + format
make lint          # Ruff checks
make type          # mypy
make db-migrate    # apply SQL migrations
make unit          # unit tests
make integration   # integration tests (depends on db-migrate)
make test          # db-migrate + lint + type + unit + integration
make dq            # GE smoke test (visible output)
make smoke         # run all smoke tests
make up            # docker compose up (db + local etl if configured)
make down          # docker compose down -v
```

---

## 🧭 Troubleshooting

* **ECR push: “repository … doesn’t exist”**
  Make sure `REPO_URL` is from TF output and not truncated; if you see `…-etl**atest**`, your tag string got mangled—re-tag then push.

* **ClusterNotFound on `run-task`:**
  Export `CLUSTER_ARN` from TF output; ensure `AWS_PROFILE`/`AWS_REGION` are set.

* **No logs:**
  Confirm log group name from TF output and tail with `aws logs tail`.

* **GE/pandas versioning:**
  The current GE harness targets **pandas < 2.0** (pinned). Upgrading pandas will require adapting `validate.py`.

---

## 📄 License

MIT (see `LICENSE`).

---

## 🧩 What’s next

* Pin immutable image tag in task definition (Terraform update).
* Private networking hardening; RDS + SSL enforcement; metrics/alarms.
* CI: lint/type/test → build → push ECR → Terraform plan/apply.
* Gold views & serving; performance tuning (bounded concurrency).
