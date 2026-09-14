# GitHub Actions Workflows

This directory contains the automated CI/CD workflows for **YoMama-as-a-Service**.

## 📋 Workflows Overview

### 🧪 CI - Tests (`ci-tests.yml`)
**Triggers:** Push to `main`/`develop`/`copilot/**`, PRs to `main`/`develop`, manual dispatch

**Jobs:**

| Job | What it does |
|-----|--------------|
| `test` | Runs the pytest suite on Python 3.10, 3.11, 3.12, 3.13 and 3.14 (matrix, `fail-fast: false`) |
| `lint` | On Python 3.14: Ruff lint, Bandit security scan, Safety vulnerability check, and uploads `bandit-report.json` as an artifact |

The tests mock the LLM layer, so no `GEMINI_API_KEY` or Ollama server is needed
in CI. Only the `test` job can fail the workflow — every step in `lint` is
`continue-on-error: true` and is advisory.

**Required Secrets:** None

---

### 🐳 Docker Build & Publish (`docker-build-publish.yml`)
**Triggers:** Push to `main`/`develop`, version tags (`v*.*.*`), PRs to `main`, manual dispatch

**What it does:**
- Builds the image from `./Dockerfile` with Buildx and a GitHub Actions cache
- On pull requests: builds `linux/amd64` only, loads it locally, and smoke-tests
  it with `python -c "import yo_mama"` — **no publish**
- On pushes and tags: builds `linux/amd64,linux/arm64` and pushes to the GitHub
  Container Registry
- Scans the pushed image with Trivy (CRITICAL/HIGH) and uploads SARIF to the
  GitHub Security tab

**Image:** `ghcr.io/chiefgyk3d/yomama-as-a-service`

**Image Tags Generated:**
- `latest` (default branch only)
- `1.2.3`, `1.2`, `1` (from `v*.*.*` git tags)
- `main` / `develop` (branch builds)
- `pr-123` (pull requests)
- `sha-<commit>`

**Required Secrets:** `GITHUB_TOKEN` (auto-provided). There is no Docker Hub
publishing — GHCR only.

---

### 🔍 PR Dependency Review (`dependency-review.yml`)
**Triggers:** PRs to `main`/`develop`

**What it does:**
- Runs `actions/dependency-review-action`, failing on **moderate** severity or above
- Posts a summary comment on the pull request

**Required Secrets:** None

---

### 🛡️ Dependency Vulnerability Scan (`dependency-scan.yml`)
**Triggers:** Every push, every PR, manual dispatch

**What it does:**
- Installs `requirements.txt` on Python 3.13
- Runs **Safety** and **pip-audit** against the resolved dependency tree
- Uploads both JSON reports as artifacts (30-day retention)

Both scans are `continue-on-error`, so this workflow reports rather than blocks.

**Required Secrets:** None

---

### 🔐 Snyk Security Scanning (`snyk-security.yml`)
**Triggers:** PRs to `main`/`develop`, weekly schedule (Mondays 00:00 UTC), manual dispatch

**What it does:**
- Snyk Code test (SAST) and Snyk Open Source test (SCA, `--severity-threshold=high`)
- Validates the generated SARIF before uploading it to the GitHub Security tab

**Required Secrets:** `SNYK_TOKEN` (get one at https://snyk.io). Without it the
scan steps no-op rather than fail.

---

### 🔎 CodeQL Analysis (`codeql-analysis.yml`)
**Triggers:** Push to `main`/`develop`, PRs to `main`/`develop`, weekly schedule (Sundays 00:00 UTC), manual dispatch

**What it does:**
- Static analysis of the Python code using the config in `.github/codeql/codeql-config.yml`
- Uploads results to the GitHub Security tab

**Required Secrets:** None (uses `GITHUB_TOKEN`)

---

## 🤖 Dependabot Configuration (`../dependabot.yml`)

Automatically opens PRs for dependency updates, all weekly on Mondays at 09:00:

- **pip** (`/` — `requirements.txt`): up to 10 open PRs, `deps` commit prefix,
  ignores major `pytest*` bumps
- **docker** (`/Docker`): up to 5 open PRs, `docker` commit prefix
- **github-actions** (`/`): up to 5 open PRs

> ⚠️ The docker ecosystem is configured for the directory `/Docker`, but this
> repository's `Dockerfile` lives at the repository root. As written, Dependabot
> will not find it and base-image updates will never be proposed.

---

## 📊 Workflow Triggers Reference

| Workflow | Push | PR | Tag | Schedule | Manual |
|----------|------|----|-----|----------|--------|
| CI - Tests | ✅ main/develop/copilot | ✅ main/develop | ❌ | ❌ | ✅ |
| Docker Build & Publish | ✅ main/develop | ✅ main (build only) | ✅ `v*.*.*` | ❌ | ✅ |
| PR Dependency Review | ❌ | ✅ main/develop | ❌ | ❌ | ❌ |
| Dependency Vulnerability Scan | ✅ all | ✅ all | ❌ | ❌ | ✅ |
| Snyk Security Scanning | ❌ | ✅ main/develop | ❌ | ✅ Weekly (Mon) | ✅ |
| CodeQL Analysis | ✅ main/develop | ✅ main/develop | ❌ | ✅ Weekly (Sun) | ✅ |

---

## 🚀 Setup Instructions

### 1. Enable GitHub Actions
Enabled by default for public repositories.

### 2. Configure Optional Secrets

```
Settings → Secrets and variables → Actions → New repository secret

SNYK_TOKEN: your_snyk_token   # Optional, enables snyk-security.yml
```

No other secrets are required — publishing uses the automatically provided
`GITHUB_TOKEN`.

### 3. GitHub Container Registry Visibility

After the first successful publish, the package appears under the repository
owner's **Packages**. Open it → *Package settings* → set visibility and link it
to this repository so `docker pull` works for your intended audience.

---

## 📊 Workflow Status Badges

These are already in the main [README](../../README.md):

```markdown
[![CI - Tests](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/ci-tests.yml)
[![Docker Build & Publish](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/docker-build-publish.yml/badge.svg)](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/docker-build-publish.yml)
[![CodeQL](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/codeql-analysis.yml)
```

---

## 🔧 Reproducing Workflows Locally

### Tests and lint

```bash
pip install -r requirements.txt
pytest tests/ -v --tb=short

pip install ruff bandit[toml] safety
ruff check yo_mama/ tests/ main.py demo.py
bandit -r yo_mama/
safety check
```

### Docker build and scan

```bash
# Build the image
docker build -t yomama-as-a-service:test .

# Same smoke test CI runs on pull requests
docker run --rm yomama-as-a-service:test python -c "import yo_mama; print('Import successful')"

# Scan it
trivy image --severity CRITICAL,HIGH yomama-as-a-service:test
```

### Using `act` (GitHub Actions local runner)

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run a specific workflow
act -W .github/workflows/ci-tests.yml
```

---

## 🛡️ Security Coverage

| Tool | Scope | Where results land |
|------|-------|--------------------|
| CodeQL | Python source (SAST) | Security tab |
| Snyk Code | Python source (SAST) | Security tab |
| Snyk Open Source | Dependencies (SCA) | Security tab |
| Trivy | Published container image | Security tab |
| Bandit | Python source | `ci-tests` artifact |
| Safety | Dependencies | `ci-tests` log + `dependency-scan` artifact |
| pip-audit | Dependencies | `dependency-scan` artifact |
| Dependency Review | Dependency changes in a PR | PR comment (blocking at moderate+) |
| Dependabot | Dependency updates | Automated PRs |

Overlap is deliberate — different databases catch different advisories, and
only Dependency Review is allowed to block a merge.

---

## 🐛 Troubleshooting

### Tests fail in CI but pass locally
- CI runs Python 3.10 through 3.14 — try the version that failed
- Check you aren't relying on a `.env` file; CI has none

### Workflow fails on pip install
- Check `requirements.txt` for version conflicts
- Confirm the pinned versions exist on PyPI for every Python in the matrix

### Docker build fails
- The Dockerfile is at the repository root (`./Dockerfile`), not in a subdirectory
- Verify every path in a `COPY` line exists and isn't excluded by `.dockerignore`

### Image published but `docker pull` says "not found"
- The package is likely still private — see *GitHub Container Registry Visibility* above
- Image names are lowercased; use `ghcr.io/chiefgyk3d/yomama-as-a-service`

### Snyk steps are skipped or empty
- `SNYK_TOKEN` is missing; the steps are intentionally non-fatal without it

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Trivy Scanner](https://aquasecurity.github.io/trivy/)
- [Snyk Documentation](https://docs.snyk.io/)
