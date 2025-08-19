## Implementation

### 0. Starter Files and Config

**Overview**
Configure the starting state of the repo and setup the environment(s) to support the solution development and packaging.

#### Tasks

- Generate repo structure
- Setup all environment and config files
- Verify the setup works cohesively

#### Acceptance criteria

- Repo is ready for *smooth* (I hope) development

#### Risks/Trade-offs

- The setup doesn't play well with each other

#### Notes and LLM Prompts

- The repo structure isn't necessarily set in stone and may need to be changed as I develop the solution
- Because of the boilerplate and lack of actual dev work in this section, most of it can be offloaded to the LLM and I'll double check after
- (prompt)  "Below is my repo so far... Please give me the full repo setup and structure I'll for the rest of the project"

**Repo Structure**
The is the starting state of the repo. Based on the extensive design and planning I put in the design doc, I was able to start off with some the basic structure of a `README.md`,  `.gitignore` my design doc and ADRs. From this I could feed them into an LLM to give me a suggested repo structure based on everything I've designed and planned for the project so far

```plaintext
tasman-dataeng-task   
 ┣ app  
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
