# Release process

`vrp-ir` publishes to PyPI through GitHub Actions and PyPI Trusted Publishing.
Merging a PR to `main` does **not** publish to PyPI by itself.

## Current release flow

1. Feature/fix/docs PRs merge to `main` in small, independently reversible
   batches.
2. `release-please.yml` runs on `main` pushes.
3. When the repository secret `RELEASE_PLEASE_TOKEN` is configured, release-please
   maintains a release PR that bumps:
   - `pyproject.toml`
   - `src/vrp_ir/__init__.py`
   - `CHANGELOG.md`
   - `.release-please-manifest.json`
4. A maintainer reviews and merges the release PR.
5. release-please creates the GitHub release and `vX.Y.Z` tag.
6. The tag triggers `publish.yml`, which builds the package and publishes to PyPI
   via OIDC Trusted Publishing.

## Required maintainer setup

`release-please.yml` needs a fine-grained user PAT stored as the repository
secret `RELEASE_PLEASE_TOKEN`.

Recommended scope:

- Repository: `zynovexllc/vrp-ir` only.
- Permissions: Contents read/write, Pull requests read/write.
- No PyPI token is required; PyPI publishing uses Trusted Publishing.

If `RELEASE_PLEASE_TOKEN` is missing, release-please logs a notice and skips.
In that state, changes on `main` remain unreleased until a maintainer either
configures the secret or performs a manual release.

## Manual release fallback

Use this only when release-please is unavailable and a maintainer explicitly
approves a release.

1. Choose the SemVer version.
2. Update `pyproject.toml`, `src/vrp_ir/__init__.py`, `CHANGELOG.md`, and
   `.release-please-manifest.json` in a release PR.
3. Wait for CI to pass.
4. Merge the release PR.
5. Create and push the tag:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

6. Confirm `publish.yml` succeeds.
7. Confirm the version appears on PyPI:

   ```bash
   python -m pip index versions vrp-ir
   ```

## Release gates

Before a release:

- `PYTHONPATH=src python3 -m unittest discover -s tests` passes.
- `python3 -m ruff check .` passes.
- The changelog describes user-visible behavior.
- No real configs or secrets are included in tests, examples, or docs.
- Any parser/audit behavior change is represented by tests with `SourceRef`
  assertions where applicable.

## Publishing expectation

PyPI is a public distribution channel. Publishing a release should be treated as
a maintainer-approved external action, not an automatic side effect of every
merge to `main`.
