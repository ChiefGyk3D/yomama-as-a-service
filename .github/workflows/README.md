# GitHub Actions Workflows

Three thin callers. The jobs themselves live in
[ChiefGyk3D/git-your-ship-together](https://github.com/ChiefGyk3D/git-your-ship-together),
shared with Stream Daemon, Typo Sniper, Star Daemon and Boon Tube Daemon, so a
pipeline fix or a new scan step lands once. Each file here says only what is
specific to YoMama-as-a-Service: Python versions, the test command, the
Dockerfile path, the CodeQL query filter, the Doppler project.

| Workflow | Triggers | Calls | What it does |
|---|---|---|---|
| `ci.yml` | push to main/develop/copilot/**, PRs, manual | `python-ci.yml` | Lint (ruff), tests on Python 3.10–3.14, Docker build with an import check, actionlint and zizmor over these files, one `CI green` gate job for branch protection |
| `release.yml` | push to main, `v*.*.*` tags, PRs, weekly, manual | `python-docker-release.yml` | Build and test on every PR; on main and tags publish a multi-arch (amd64 + arm64) image to `ghcr.io/chiefgyk3d/yomama-as-a-service`, signed with cosign, with a syft SBOM attached and SLSA provenance recorded; Trivy scan to the Security tab |
| `security.yml` | push to main/develop, PRs, weekly, manual | `security.yml` | CodeQL (`security-extended,security-and-quality`, with the two clear-text alerts excluded for `yo_mama/secrets.py`), gitleaks over the full history, pip-audit, dependency review on PRs, Snyk |

## Secrets: Doppler, not GitHub

No secret is stored in this repository's GitHub secrets. A job authenticates
to Doppler with a short-lived token minted from its own GitHub OIDC identity
(a Doppler Service Account Identity) and reads the `ci` config of the shared
`ci` Doppler project, which holds only what the pipelines need:

| Name | Used by |
|---|---|
| `SNYK_TOKEN` | `security.yml`, Snyk |

GHCR publishing uses the job's own `GITHUB_TOKEN` and needs nothing from
Doppler. Docker Hub is not a publish target; setting `dockerhub: true` in
`release.yml` and adding `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` to the
config would make it one.

The one per-repository setting is the **repository variable**
`DOPPLER_IDENTITY_ID` (Settings → Secrets and variables → Actions →
Variables), the UUID of the identity. It is an identifier, not a secret.

Before that is set the pipelines still run: Snyk warns and skips, everything
else is unaffected.

The setup runbook, the fallback path (a Doppler Service Token as the single
GitHub secret `DOPPLER_TOKEN`), and every input are documented in the
git-your-ship-together README.

## Verifying a published image

```sh
cosign verify ghcr.io/chiefgyk3d/yomama-as-a-service:latest \
  --certificate-identity-regexp '^https://github.com/ChiefGyk3D/git-your-ship-together/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

gh attestation verify oci://ghcr.io/chiefgyk3d/yomama-as-a-service:latest --owner ChiefGyk3D
```

The SBOM is also attached to every run of `release.yml` as the
`sbom.spdx.json` artifact.

## Image tags

- `latest` (main branch only)
- `1.2.3`, `1.2`, `1` (from `v1.2.3` tags)
- `main`, `sha-<short>` (branch and commit)
- `pr-123` (pull requests; built and tested, never pushed)

## Dependabot

`dependabot.yml` opens weekly PRs for Python packages, the Docker base image
(digest-pinned in the root `Dockerfile`) and GitHub Actions, each with a
seven-day cooldown on new releases.

## Status badges

```markdown
[![CI](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/ci.yml/badge.svg)](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/ci.yml)
[![Release](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/release.yml/badge.svg)](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/release.yml)
[![Security](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/security.yml/badge.svg)](https://github.com/ChiefGyk3D/yomama-as-a-service/actions/workflows/security.yml)
```

## What changed in the migration

- `ci-tests.yml`, `docker-build-publish.yml`, `codeql-analysis.yml`,
  `dependency-review.yml`, `dependency-scan.yml` and `snyk-security.yml` were
  replaced by the three callers above. `.github/codeql/codeql-config.yml`
  moved inline into `security.yml` as `codeql-config`.
- Bandit and `safety check` were dropped: `safety check` is deprecated
  upstream and needs an account, and both ran as advisory-only. CodeQL and
  ruff's `S` rules (`ruff.toml`) cover SAST and pip-audit covers the advisory
  database.
- pip-audit gates. Ruff lint stays advisory (`lint-continue-on-error`) until
  the tree is clean; delete that line to make it gate.
- `develop` no longer triggers a container build; `release.yml` publishes
  from `main` and version tags only, and runs weekly so base-image fixes
  reach `latest` between commits.
- Images are now signed, carry an SBOM and provenance, and a publishing
  build never reads the GitHub Actions cache.
