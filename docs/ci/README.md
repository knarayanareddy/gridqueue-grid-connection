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
