# CI workflow

`github-ci.yml` is the project's CI definition. It is kept here rather than in `.github/workflows/` because the
token used to push the initial scaffold lacked the `workflow` scope, and GitHub rejects pushes that create or
modify workflow files without it.

**To enable CI** (one-time, by a maintainer):

1. On GitHub, open *Add file → Create new file*, name it `.github/workflows/ci.yml`.
2. Paste the contents of `docs/ci/github-ci.yml` and commit to `main`.

Or locally, with a token that has the `workflow` scope:

```bash
mkdir -p .github/workflows && cp docs/ci/github-ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml && git commit -m "ci: enable workflow" && git push
```

Once it exists, re-add the CI badge to the top of `README.md`:

```markdown
[![CI](https://github.com/knarayanareddy/gridqueue-grid-connection/actions/workflows/ci.yml/badge.svg)](https://github.com/knarayanareddy/gridqueue-grid-connection/actions/workflows/ci.yml)
```

## GitHub Pages (static demo)

`deploy-pages.yml` builds the static demo (`make build-pages`: snapshot from `scripts/build_static_demo.py`, then
`vite build --mode pages` with base `/gridqueue-grid-connection/`) and deploys `frontend/dist` to
https://knarayanareddy.github.io/gridqueue-grid-connection/ on every push to `main` (or manually via
*Run workflow*). Actions are pinned to their current major versions (checkout v7, setup-uv v10.3.2,
setup-node v7, configure-pages v6, upload-pages-artifact v5, deploy-pages v5).

**To enable** (one-time, by a maintainer):

1. *Settings → Pages → Build and deployment → Source: GitHub Actions*; or
   `gh api -X POST repos/knarayanareddy/gridqueue-grid-connection/pages -f build_type=workflow`.
2. If it is not already there, copy `docs/ci/deploy-pages.yml` to `.github/workflows/deploy-pages.yml` (same
   `workflow` scope caveat as above) and push to `main`.

Check locally first: `make build-pages && make pages-preview` serves the same build on port 4173.
