"""Development workflow controls preserve release admission and source identity."""

import os
from pathlib import Path
import subprocess

import pytest
import yaml


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/pypi-publish-and-github-release-on-tag.yml"


@pytest.mark.parametrize("job", ["frontend", "test", "build"])
@pytest.mark.parametrize("tag", ["v0.44.6", "$(touch CANARY)", "v0.44.6;touch CANARY", "v0.44.6\nother"])
def test_manual_release_tag_is_data_and_refuses_noncanonical_versions(tmp_path, job, tag):
    # Arrange
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    step = next(s for s in jobs[job]["steps"] if s.get("id") == "ver")
    output = tmp_path / "output"
    output.write_text("")
    env = dict(os.environ, GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_OUTPUT=str(output),
               FIGRECIPE_RELEASE_TAG=tag)
    script = step["run"].replace("${{ github.event_name }}", "workflow_dispatch").replace("${{ inputs.version }}", tag)
    # Act
    result = subprocess.run(["bash", "-euo", "pipefail"], input=script, text=True,
                            cwd=tmp_path, env=env, capture_output=True, timeout=5)
    # Assert
    assert (result.returncode == 0, (tmp_path / "CANARY").exists(),
            output.read_text() == "version=v0.44.6\n") == (
        tag == "v0.44.6", False, tag == "v0.44.6")


@pytest.mark.parametrize("job", ["frontend", "test", "build", "publish", "release", "sync-main"])
def test_every_release_job_requires_admitted_organization_cpu_destination(job):
    # Arrange
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    # Act
    route = str(jobs[job]["runs-on"])
    # Assert
    assert ("runner-admission" in jobs[job]["needs"], "native_authorized" in route,
            '"group":"Organization"' in route, "scitex-org-cpu" in route,
            jobs.get("runner-admission", {}).get("permissions")) == (True, True, True, True, {})


def test_publisher_is_bound_to_the_build_source_and_original_delivery_gates():
    # Arrange
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    # Act
    publish = jobs["publish"]
    checkout = next(s for s in publish["steps"] if s.get("uses") == "actions/checkout@v4")
    # Assert
    assert (checkout["with"], jobs["build"]["needs"], publish["needs"],
            publish["permissions"], publish["environment"]["name"]) == (
        {"ref": "${{ needs.build.outputs.source_sha }}"}, ["test", "frontend", "runner-admission"],
        ["build", "runner-admission"], {"id-token": "write"}, "pypi")


@pytest.mark.parametrize("job", ["test", "build"])
def test_source_must_belong_to_main_before_release_execution(job):
    # Arrange
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"][job]["steps"]
    # Act
    checkout_index = next(i for i, s in enumerate(steps) if s.get("uses") == "actions/checkout@v4")
    verification = next((s for s in steps[checkout_index + 1:]
                         if "git merge-base --is-ancestor HEAD origin/main" in s.get("run", "")), None)
    # Assert
    assert verification is not None


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Release fixture",
         "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
         "-c", "core.hooksPath=/dev/null", *args],
        check=True, capture_output=True, text=True, timeout=5,
    )


def _promoted_repo(tmp_path, job):
    repo = tmp_path / "figrecipe" if job == "frontend" else tmp_path
    repo.mkdir(exist_ok=True)
    _git(repo, "init", "-q")
    (repo / "proof").write_text("accepted")
    _git(repo, "add", "proof")
    _git(repo, "commit", "-qm", "accepted fixture")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _check_ancestry(tmp_path, job):
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"][job]["steps"]
    script = next(s["run"] for s in steps if "--is-ancestor" in s.get("run", ""))
    env = dict(os.environ, GITHUB_OUTPUT=str(tmp_path / "output"))
    return subprocess.run(["bash", "-euo", "pipefail"], input=script, text=True,
                          cwd=tmp_path, env=env, capture_output=True, timeout=5)


@pytest.mark.parametrize("job", ["frontend", "test", "build"])
def test_actual_main_ancestry_check_accepts_promoted_source(tmp_path, job):
    # Arrange
    _promoted_repo(tmp_path, job)
    # Act
    result = _check_ancestry(tmp_path, job)
    # Assert
    assert result.returncode == 0


@pytest.mark.parametrize("job", ["frontend", "test", "build"])
def test_actual_main_ancestry_check_refuses_unpromoted_source(tmp_path, job):
    # Arrange
    repo = _promoted_repo(tmp_path, job)
    (repo / "proof").write_text("not promoted")
    _git(repo, "commit", "-qam", "unpromoted fixture")
    # Act
    result = _check_ancestry(tmp_path, job)
    # Assert
    assert result.returncode != 0
