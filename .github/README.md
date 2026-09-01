# .github — CI/CD and Automation

This repository is private and not public-ready.

---

## CI Pipeline — `workflows/ci.yml`

Runs on every push to `main` and on every pull request.

| Job | What it does |
|---|---|
| `compile-and-validate` | Python 3.12 syntax check (`py_compile`), `pyproject.toml` TOML validation, YAML config file validation. |
| `unit-tests` | Runs `pytest backend/tests/unit -m unit -v --tb=short`. No `.env`, `sales.db`, IBM Cloud, COS, watsonx, or secrets required. |
| `docker-build` | Builds the Docker image from `backend/Dockerfile`. Does not run the container and does not require any secrets. |

---

## Deployment — `workflows/deploy-code-engine.yml`

Manual trigger (`workflow_dispatch`) only. Builds the Docker image, pushes it to IBM Container Registry, and updates the IBM Code Engine application to use the new image. Runtime environment variables and secrets are managed in Code Engine directly; this workflow does not read or modify them.

Requires the `IBM_CLOUD_API_KEY` GitHub secret and several GitHub repository variables to be configured before use. See the main `README.md` for prerequisites.

---

## Dependency Automation — `dependabot.yml`

Dependabot monitors three ecosystems weekly (Monday):

- Python pip dependencies (`backend/requirements.txt`).
- GitHub Actions workflow versions.
- Docker base image in `backend/Dockerfile` (minor Python version updates are excluded; runtime version changes are handled as deliberate compatibility tasks).

Dependabot opens update PRs according to the repository configuration.
