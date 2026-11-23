# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-11-23

### Added
- Warn when a secret or variable is defined only for an environment, but a job that uses it doesn't set that environment. These count toward exit status 1, like missing names

## [0.3.0] - 2026-11-18

### Added
- Unused secrets and variables show when they were last updated, oldest first, in every output format

## [0.2.0] - 2026-11-12

### Added
- `--markdown` prints the report as Markdown tables, ready to paste into an issue or pull request

## [0.1.0] - 2026-10-29

### Added
- Find secrets and variables used in workflows but not defined, and ones defined but never used
- Repository, environment, organization and Dependabot sources
- Reusable workflow (`workflow_call`) secret inputs handled correctly
- Local or remote workflow reading, table or JSON output, CI-friendly exit codes
