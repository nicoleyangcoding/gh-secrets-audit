# Contributing

Thanks for helping. Small pull requests are easiest to review.

## Development setup

```bash
git clone https://github.com/nicoleyangcoding/gh-secrets-audit
cd gh-secrets-audit
python -m venv .venv && source .venv/bin/activate
pip install pytest ruff
pytest
ruff check . && ruff format --check .
gh extension install .       # try your local copy as `gh secrets-audit`
```

The extension is a single file, `gh-secrets-audit`, so `gh extension install` works without a build step. Keep it that way: standard library only.

## Guidelines

- Never read, print or log anything except secret names.
- Call `gh` with argument lists, never through a shell.
