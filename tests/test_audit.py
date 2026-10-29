from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "gh-secrets-audit"
loader = importlib.machinery.SourceFileLoader("gh_secrets_audit", str(SCRIPT))
spec = importlib.util.spec_from_loader("gh_secrets_audit", loader)
audit_mod = importlib.util.module_from_spec(spec)
sys.modules["gh_secrets_audit"] = audit_mod  # dataclasses look the module up while loading
loader.exec_module(audit_mod)

DEPLOY = """name: Deploy
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      # - run: echo ${{ secrets.COMMENTED_OUT }}
      - run: ./deploy.sh
        env:
          TOKEN: ${{ secrets.DEPLOY_TOKEN }}
          URL: ${{ vars.SITE_URL }}
          GH: ${{ secrets.GITHUB_TOKEN }}
          KEY: ${{ secrets['signing_key'] }}
          ALSO: ${{ secrets . SPACED }}
"""

REUSABLE = """on:
  workflow_call:
    inputs:
      env:
        type: string
    secrets:
      NPM_TOKEN:
        required: true
      registry-password:
        required: false
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
          PASS: ${{ secrets.REGISTRY-PASSWORD }}
          SENTRY: ${{ secrets.SENTRY_DSN }}
"""


def test_scan_finds_references_and_skips_builtins_and_comments():
    refs = audit_mod.scan_workflow(DEPLOY, "deploy.yml")
    found = {(r.kind, r.name) for r in refs}
    assert found == {
        ("secret", "DEPLOY_TOKEN"),
        ("variable", "SITE_URL"),
        ("secret", "SIGNING_KEY"),
        ("secret", "SPACED"),
    }
    assert next(r for r in refs if r.name == "DEPLOY_TOKEN").line == 11


def test_reusable_workflow_inputs_are_not_repo_secrets():
    assert audit_mod._workflow_call_secrets(REUSABLE.splitlines()) == {"NPM_TOKEN", "REGISTRY-PASSWORD"}
    refs = audit_mod.scan_workflow(REUSABLE, "publish.yml")
    assert [r.name for r in refs] == ["SENTRY_DSN"]


def defined(**sources):
    d = audit_mod.Defined()
    for source, names in sources.items():
        for kind_name in names:
            kind, name = kind_name.split(":")
            d.add(kind, name, source.replace("_", ": ") if source.startswith("environment") else source)
    return d


def test_audit_missing_unused_and_org_rules():
    refs = audit_mod.scan_workflow(DEPLOY, "deploy.yml")
    result = audit_mod.audit(
        refs,
        defined(
            repo=["secret:deploy_token", "secret:OLD_TOKEN", "variable:SITE_URL"],
            organization=["secret:SIGNING_KEY", "secret:ORG_ONLY"],
            environment_production=["secret:SPACED", "variable:UNUSED_VAR"],
        ),
    )
    assert list(result.missing) == []
    assert set(result.unused) == {("secret", "OLD_TOKEN"), ("variable", "UNUSED_VAR")}
    assert result.unused[("variable", "UNUSED_VAR")] == {"environment: production"}
    assert result.used == 4


def test_audit_reports_missing_with_locations():
    refs = audit_mod.scan_workflow(DEPLOY, "deploy.yml") + audit_mod.scan_workflow(DEPLOY, "again.yml")
    result = audit_mod.audit(refs, defined(repo=["variable:SITE_URL"]))
    assert ("secret", "DEPLOY_TOKEN") in result.missing
    text = audit_mod.render(result, "o/r")
    assert "Missing: used in workflows but not defined" in text
    assert "deploy.yml:11" in text and "again.yml:11" in text


class FakeGitHub:
    """Stands in for the gh CLI. Paths map to names; None means HTTP 403."""

    def __init__(self, repo, data=None, workflows=None):
        self.repo = repo
        self.data = data or {}
        self.workflows = workflows or {}

    def names(self, path, key):
        return self.data.get(path.split(f"{self.repo}/", 1)[1], [])

    def environments(self):
        return self.data.get("environments", [])

    def remote_workflows(self):
        return self.workflows


def run_main(capsys, data, workflows, *extra):
    def factory(repo):
        return FakeGitHub(repo, data, workflows)

    code = audit_mod.main(["-R", "o/r", *extra], api_factory=factory)
    return code, capsys.readouterr()


def test_main_exit_codes_and_json(capsys):
    workflows = {"deploy.yml": DEPLOY}
    data = {
        "actions/secrets": ["DEPLOY_TOKEN", "SIGNING_KEY", "SPACED", "STALE"],
        "actions/variables": ["SITE_URL"],
        "environments": ["production"],
        "environments/production/secrets": [],
        "environments/production/variables": [],
    }
    code, out = run_main(capsys, data, workflows)
    assert code == 0 and "STALE" in out.out
    code, out = run_main(capsys, data, workflows, "--fail-on-unused")
    assert code == 1
    data["actions/secrets"] = ["SIGNING_KEY"]
    code, out = run_main(capsys, data, workflows, "--json")
    report = json.loads(out.out)
    assert code == 1
    assert {m["name"] for m in report["missing"]} == {"DEPLOY_TOKEN", "SPACED"}


def test_unreadable_sources_are_reported(capsys):
    data = {
        "actions/secrets": ["DEPLOY_TOKEN"],
        "actions/variables": ["SITE_URL"],
        "dependabot/secrets": None,
    }
    code, out = run_main(capsys, data, {"deploy.yml": DEPLOY})
    assert "Couldn't read: dependabot secrets" in out.out


def test_no_access_is_an_error_not_all_good(capsys):
    data = {"actions/secrets": None, "actions/variables": None}
    code, out = run_main(capsys, data, {"deploy.yml": DEPLOY})
    assert code == 2 and "needs admin access" in out.err and "All good" not in out.out


def test_no_workflows(capsys):
    code, out = run_main(capsys, {}, {})
    assert code == 0 and "No workflow files found" in out.out


def test_local_workflows(tmp_path):
    folder = tmp_path / ".github" / "workflows"
    folder.mkdir(parents=True)
    (folder / "a.yml").write_text("x")
    (folder / "b.yaml").write_text("y")
    (folder / "notes.md").write_text("z")
    assert set(audit_mod.local_workflows(tmp_path)) == {"a.yml", "b.yaml"}


def test_script_runs_as_executable():
    result = subprocess.run([str(SCRIPT), "--version"], capture_output=True, text=True, check=False)
    assert result.stdout.strip() == f"gh-secrets-audit {audit_mod.__version__}"


@pytest.mark.parametrize("line", ["${{ secrets.FOO }}", "${{ secrets['FOO'] }}", '${{ secrets["foo"] }}'])
def test_reference_styles(line):
    (ref,) = audit_mod.scan_workflow(f"run: echo {line}", "w.yml")
    assert ref.name == "FOO"
