from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Protocol

from .editing import EditError, apply_candidate
from .models import Candidate, TestResult


class Sandbox(Protocol):
    name: str

    def baseline(self, repo: Path, test_command: str) -> TestResult: ...
    def evaluate(self, repo: Path, candidate: Candidate, test_command: str) -> TestResult: ...


_SECRET_MARKERS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "AUTH")
_COPY_IGNORES = (
    ".git",
    ".git*",
    ".env",
    ".env.*",
    ".venv",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
    ".ssh",
    ".aws",
    ".npmrc",
    ".pypirc",
    ".netrc",
)


def _sanitized_env() -> dict[str, str]:
    """Return a host environment with likely credentials removed."""
    env = dict(os.environ)
    for key in list(env):
        upper = key.upper()
        if any(marker in upper for marker in _SECRET_MARKERS):
            env.pop(key, None)
    return env


def _copy_repo(repo: Path, destination: Path) -> None:
    shutil.copytree(repo, destination, ignore=shutil.ignore_patterns(*_COPY_IGNORES))


def _is_excluded(path: Path, repo: Path) -> bool:
    rel = path.relative_to(repo)
    for part in rel.parts:
        if part in {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", "dist", "build", ".ssh", ".aws"}:
            return True
        if part.startswith(".env") or part.startswith(".git"):
            return True
    return path.name in {".npmrc", ".pypirc", ".netrc"} or path.suffix == ".pyc"


def _run_local(command: str, cwd: Path, *, timeout_seconds: int, deny_network: bool) -> TestResult:
    argv = ["/bin/sh", "-lc", command]
    branch = cwd.name
    if deny_network and platform.system() == "Darwin" and shutil.which("sandbox-exec"):
        profile = "(version 1)(allow default)(deny network*)"
        argv = [shutil.which("sandbox-exec") or "/usr/bin/sandbox-exec", "-p", profile, *argv]
    try:
        p = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            env=_sanitized_env(),
        )
        return TestResult(p.returncode, p.stdout, p.stderr, branch)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        suffix = f"BranchSmith timeout after {timeout_seconds}s"
        return TestResult(124, stdout, (stderr + "\n" + suffix).strip(), branch)


class LocalSandbox:
    """Independent temporary workspaces with secret stripping and optional network denial."""

    name = "local-isolated-workspace"

    def __init__(self, *, timeout_seconds: int = 120, deny_network: bool = True):
        self.timeout_seconds = timeout_seconds
        self.deny_network = deny_network

    def _run_copy(self, repo: Path, test_command: str, branch_name: str, candidate: Candidate | None = None) -> TestResult:
        with tempfile.TemporaryDirectory(prefix="branchsmith-") as td:
            branch = Path(td) / branch_name
            _copy_repo(repo, branch)
            if candidate is not None:
                try:
                    apply_candidate(branch, candidate)
                except EditError as exc:
                    return TestResult(97, "", str(exc), branch_name)
            result = _run_local(
                test_command,
                branch,
                timeout_seconds=self.timeout_seconds,
                deny_network=self.deny_network,
            )
            return TestResult(result.exit_code, result.stdout, result.stderr, branch_name)

    def baseline(self, repo: Path, test_command: str) -> TestResult:
        return self._run_copy(repo.resolve(), test_command, "baseline")

    def evaluate(self, repo: Path, candidate: Candidate, test_command: str) -> TestResult:
        return self._run_copy(repo.resolve(), test_command, candidate.candidate_id, candidate)


class DockerSandbox:
    """Container fallback with no network, CPU/memory bounds, and per-candidate workspaces."""

    name = "docker-isolated-workspace"

    def __init__(
        self,
        *,
        image: str = "python:3.11-slim",
        timeout_seconds: int = 120,
        cpus: float = 1.0,
        memory: str = "1g",
    ):
        self.docker = shutil.which("docker")
        if not self.docker:
            raise RuntimeError("docker CLI not found")
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.cpus = cpus
        self.memory = memory

    def _run_copy(self, repo: Path, test_command: str, branch_name: str, candidate: Candidate | None = None) -> TestResult:
        with tempfile.TemporaryDirectory(prefix="branchsmith-docker-") as td:
            branch = Path(td) / branch_name
            _copy_repo(repo, branch)
            if candidate is not None:
                try:
                    apply_candidate(branch, candidate)
                except EditError as exc:
                    return TestResult(97, "", str(exc), branch_name)
            argv = [
                self.docker,
                "run",
                "--rm",
                "--network",
                "none",
                "--cpus",
                str(self.cpus),
                "--memory",
                self.memory,
                "-v",
                f"{branch}:/workspace:rw",
                "-w",
                "/workspace",
                self.image,
                "/bin/sh",
                "-lc",
                test_command,
            ]
            try:
                p = subprocess.run(
                    argv,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    env=_sanitized_env(),
                )
                return TestResult(p.returncode, p.stdout, p.stderr, branch_name)
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr = exc.stderr if isinstance(exc.stderr, str) else ""
                return TestResult(
                    124,
                    stdout,
                    (stderr + f"\nBranchSmith timeout after {self.timeout_seconds}s").strip(),
                    branch_name,
                )

    def baseline(self, repo: Path, test_command: str) -> TestResult:
        return self._run_copy(repo.resolve(), test_command, "baseline")

    def evaluate(self, repo: Path, candidate: Candidate, test_command: str) -> TestResult:
        return self._run_copy(repo.resolve(), test_command, candidate.candidate_id, candidate)


class ContreeSandbox:
    """Nebius Token Factory Sandboxes adapter using the official contree CLI."""

    name = "nebius-token-factory-contree"

    def __init__(self, *, session: str | None = None, image: str = "tag:python:3.11-slim"):
        if shutil.which("contree") is None:
            raise RuntimeError("contree CLI not found; install live dependencies and run contree auth")
        self.session = session or f"branchsmith-{uuid.uuid4().hex[:10]}"
        self.image = image
        self._prepared_repo: Path | None = None
        self._baseline: TestResult | None = None

    def _cmd(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        p = subprocess.run(["contree", "-S", self.session, *args], text=True, capture_output=True)
        if check and p.returncode != 0:
            raise RuntimeError(f"contree command failed: {' '.join(args)}\n{p.stderr}")
        return p

    def _stage_repo(self, repo: Path) -> None:
        for src in sorted(repo.rglob("*")):
            if not src.is_file() or _is_excluded(src, repo):
                continue
            rel = src.relative_to(repo).as_posix()
            self._cmd("file", "cp", str(src), f"/workspace/{rel}", check=True)

    def baseline(self, repo: Path, test_command: str) -> TestResult:
        repo = repo.resolve()
        self._cmd("use", self.image, check=True)
        self._stage_repo(repo)
        self._cmd("run", "-C", "/workspace", "--", "/bin/true", check=True)
        p = self._cmd("run", "-D", "-C", "/workspace", "-s", "--", test_command)
        self._prepared_repo = repo
        self._baseline = TestResult(p.returncode, p.stdout, p.stderr, "main")
        return self._baseline

    def evaluate(self, repo: Path, candidate: Candidate, test_command: str) -> TestResult:
        if self._prepared_repo != repo.resolve() or self._baseline is None:
            raise RuntimeError("baseline() must be called before evaluate()")
        safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in candidate.candidate_id)[:40]
        branch_name = f"cand-{safe_id}-{uuid.uuid4().hex[:6]}"
        self._cmd("session", "checkout", "main", check=True)
        self._cmd("session", "branch", branch_name, "--from", "main", check=True)
        self._cmd("session", "checkout", branch_name, check=True)
        with tempfile.TemporaryDirectory(prefix="branchsmith-edit-") as td:
            work = Path(td) / "repo"
            _copy_repo(repo, work)
            try:
                changed = apply_candidate(work, candidate)
            except EditError as exc:
                return TestResult(97, "", str(exc), branch_name)
            for path in changed:
                rel = path.relative_to(work).as_posix()
                self._cmd("file", "cp", str(path), f"/workspace/{rel}", check=True)
            p = self._cmd("run", "-C", "/workspace", "-s", "--", test_command)
        return TestResult(p.returncode, p.stdout, p.stderr, branch_name)


def _contree_ready() -> bool:
    contree = shutil.which("contree")
    if not contree:
        return False
    try:
        p = subprocess.run(
            [contree, "-o", "json", "images", "--prefix=python"],
            text=True,
            capture_output=True,
            timeout=10,
        )
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def select_sandbox(
    kind: str,
    *,
    session: str | None = None,
    timeout_seconds: int = 120,
    docker_image: str = "python:3.11-slim",
    allow_network: bool = False,
) -> Sandbox:
    if kind == "contree":
        return ContreeSandbox(session=session)
    if kind == "docker":
        return DockerSandbox(image=docker_image, timeout_seconds=timeout_seconds)
    if kind == "local":
        return LocalSandbox(timeout_seconds=timeout_seconds, deny_network=not allow_network)
    if kind != "auto":
        raise ValueError(f"unknown sandbox backend: {kind}")

    if _contree_ready():
        return ContreeSandbox(session=session)
    if shutil.which("docker"):
        return DockerSandbox(image=docker_image, timeout_seconds=timeout_seconds)
    return LocalSandbox(timeout_seconds=timeout_seconds, deny_network=not allow_network)
