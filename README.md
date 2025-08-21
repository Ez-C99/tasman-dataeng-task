# Tasman Data Engineering Task — USAJOBS ETL

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

## 🗺️ Repo at a glance

```plaintext
src/
  tasman_etl/
    config.py                # dotenv helpers (env / DB URL / settings)
    http/usajobs.py          # resilient USAJOBS client (backoff + headers)
    storage/bronze_s3.py     # put_json_gz(), bronze_key(), utc_now_iso()
    models.py                # Pydantic v2 DTOs for raw + normalised
    transform.py             # normalise_page() -> Bundles
    db/
      migrations/001_init.sql
      engine.py              # psycopg engine wrapper
      repository.py          # upsert_page() + helpers
    dq/gx/validate.py        # Great Expectations validation (pandas)
    runner/run.py            # ingest_search_page() orchestration
tests/
  unit/, integration/, smoke/
infra/terraform/             # ECS/ECR/EventBridge/S3/IAM
docker/
  Dockerfile, docker-compose.yml
Makefile, pyproject.toml, .env.example, DESIGN_DOC.md, DEV_LOG.md
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
LOCATION_NAME=Chicago, Illinois
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
* `schedule_expression` (default hourly: `cron(0 * * * ? *)`)
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

## 🙌 Acknowledgements

* USAJOBS API
* Great Expectations
* Postgres / psycopg
* AWS ECS, ECR, EventBridge, CloudWatch, S3

---

## 🧩 What’s next

* Pin immutable image tag in task definition (Terraform update).
* Private networking hardening; RDS + SSL enforcement; metrics/alarms.
* CI: lint/type/test → build → push ECR → Terraform plan/apply.
* Gold views & serving; performance tuning (bounded concurrency).
