# Roadmap

Small, focused releases. Suggestions are welcome in [issues](https://github.com/nicoleyangcoding/gh-secrets-audit/issues).

## 0.2
- [ ] Warn when a job uses an environment secret but the job doesn't set that `environment:`
- [ ] `--org ORG`: audit every repository in an organization and summarize
- [ ] Check composite actions in the repo (`action.yml`) for `inputs` that look like secrets

## 0.3
- [ ] Show when each unused secret was last updated (`updated_at`), oldest first
- [x] Markdown output for pasting into an issue
- [ ] GitHub Action wrapper for a scheduled monthly audit

## Not planned
- Reading or rotating secret values. This tool only ever deals with names.
