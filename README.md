# gh-secrets-audit

A GitHub CLI extension that finds GitHub Actions secrets and variables that are **missing** (your workflows use them but they aren't defined) or **unused** (defined, but nothing uses them anymore).

A missing secret quietly becomes an empty string, and a deploy fails in a confusing way. An unused secret is a credential that no longer needs to exist. One command shows both.

```
$ gh secrets-audit
Missing: used in workflows but not defined
  NPM_TOKEN      secret    release.yml:41
  SENTRY_DSN     secret    deploy.yml:23, deploy.yml:57

Unused: defined but not referenced by any workflow
  OLD_HEROKU_KEY secret    repo
  STAGING_URL    variable  environment: staging

2 missing, 2 unused, 7 in use and defined.
```

## Install

Requires the [GitHub CLI](https://cli.github.com) and Python 3.9 or newer.

```bash
gh extension install nicoleyangcoding/gh-secrets-audit
```

## Use

```bash
cd your-repo
gh secrets-audit                    # audit the repo you're in
gh secrets-audit -R owner/repo      # audit any repo you administer
gh secrets-audit --json             # machine-readable
gh secrets-audit --fail-on-unused   # exit 1 on unused names too
```

Exit status is `1` when something is missing (or unused, with `--fail-on-unused`), `0` when everything checks out, and `2` when the audit couldn't run.

## What it checks

It reads every file in `.github/workflows/`: from your local clone when you're in one, or from GitHub with `-R` or `--remote`. It collects each `secrets.NAME`, `secrets['NAME']` and `vars.NAME`, then compares those names with what's defined:

| Defined in | Counts toward "missing" | Reported as "unused" |
| --- | --- | --- |
| Repository secrets and variables | yes | yes |
| Environment secrets and variables | yes | yes |
| Organization secrets and variables shared with the repo | yes | no (other repos may use them) |
| Dependabot secrets | yes | yes |

It also understands that:

- `secrets.GITHUB_TOKEN` is built in.
- In a reusable workflow, secrets declared under `on: workflow_call: secrets:` are passed in by the caller and aren't repository secrets.
- Names are case-insensitive, as they are on GitHub.
- Commented-out lines don't count.

## Privacy and permissions

- Read-only. It never creates, changes or deletes anything.
- GitHub's API only returns secret **names**. Values are never available to this tool or anyone else.
- Listing secret names requires admin access to the repository. If you don't have it, the tool says so instead of guessing.

## Limitations

A secret that is only used by something outside workflows, like Codespaces or a third-party integration, will show as unused. Check before deleting anything.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [roadmap](ROADMAP.md).

## License

[MIT](LICENSE)
