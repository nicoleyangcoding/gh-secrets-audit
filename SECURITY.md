# Security policy

`gh-secrets-audit` is read-only. It calls the GitHub API through the `gh` CLI to list secret and variable names (GitHub never exposes values) and reads workflow files. It writes nothing.

If you find a security problem, please report it privately through [GitHub's private vulnerability reporting](https://github.com/nicoleyangcoding/gh-secrets-audit/security/advisories/new) rather than opening a public issue. You can expect a reply within 7 days.
