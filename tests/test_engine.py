import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from branchsmith.editing import EditError, apply_candidate
from branchsmith.engine import run_repair
from branchsmith.models import Candidate, Edit
from branchsmith.planner import DemoPlanner, _extract_json
from branchsmith.sandbox import LocalSandbox, _sanitized_env, select_sandbox


class EngineTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        (root / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        (root / "test_calc.py").write_text(
            "import unittest\nfrom calc import add\n"
            "class T(unittest.TestCase):\n"
            "    def test_add(self): self.assertEqual(add(2,3),5)\n"
            "if __name__ == '__main__': unittest.main()\n",
            encoding="utf-8",
        )
        return root

    def test_offline_vertical_slice_selects_passing_branch(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            report = run_repair(
                repo=repo,
                issue="add returns subtraction",
                test_command="python -m unittest -q",
                planner=DemoPlanner(),
                sandbox=LocalSandbox(),
                candidate_count=3,
            )
            self.assertFalse(report.baseline.passed)
            self.assertEqual(report.winner_id, "swap-minus-to-plus")
            self.assertEqual(sum(r.test.passed for r in report.candidates), 1)
            self.assertEqual(report.sandbox, "local-isolated-workspace")

    def test_fenced_json_is_parsed(self):
        fence = chr(96) * 3
        raw = fence + "json\n{\"candidates\": []}\n" + fence
        self.assertEqual(_extract_json(raw), {"candidates": []})

    def test_edit_must_be_unique(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "x.py").write_text("x = 1\nx = 1\n", encoding="utf-8")
            c = Candidate("x", "", (Edit("x.py", "x = 1", "x = 2"),))
            with self.assertRaises(EditError):
                apply_candidate(root, c)

    def test_edit_cannot_escape_repo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = Candidate("x", "", (Edit("../escape", "a", "b"),))
            with self.assertRaises(EditError):
                apply_candidate(root, c)

    def test_candidate_cannot_edit_tests(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "test_x.py").write_text("assert False\n", encoding="utf-8")
            c = Candidate("x", "", (Edit("test_x.py", "False", "True"),))
            with self.assertRaises(EditError):
                apply_candidate(root, c)

    def test_local_baseline_does_not_mutate_source_repo(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            result = LocalSandbox(deny_network=False).baseline(
                repo,
                "printf '\\n# mutation' >> calc.py; exit 1",
            )
            self.assertFalse(result.passed)
            self.assertNotIn("mutation", (repo / "calc.py").read_text(encoding="utf-8"))

    def test_local_timeout_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            result = LocalSandbox(timeout_seconds=1, deny_network=False).baseline(repo, "sleep 3")
            self.assertEqual(result.exit_code, 124)
            self.assertIn("timeout", result.stderr.lower())

    def test_secret_like_environment_variables_are_removed(self):
        with mock.patch.dict(os.environ, {"NEBIUS_API_KEY": "secret", "NORMAL_SETTING": "ok"}, clear=False):
            env = _sanitized_env()
        self.assertNotIn("NEBIUS_API_KEY", env)
        self.assertEqual(env["NORMAL_SETTING"], "ok")

    def test_auto_backend_falls_back_to_local(self):
        with mock.patch("branchsmith.sandbox._contree_ready", return_value=False), mock.patch(
            "branchsmith.sandbox.shutil.which", return_value=None
        ):
            sandbox = select_sandbox("auto")
        self.assertIsInstance(sandbox, LocalSandbox)

    def test_docker_backend_disables_network(self):
        from branchsmith.sandbox import DockerSandbox

        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            fake = mock.Mock(returncode=1, stdout="", stderr="expected failure")
            with mock.patch("branchsmith.sandbox.shutil.which", return_value="/usr/bin/docker"), mock.patch(
                "branchsmith.sandbox.subprocess.run", return_value=fake
            ) as run:
                result = DockerSandbox().baseline(repo, "python -m unittest -q")
            argv = run.call_args.args[0]
            self.assertIn("--network", argv)
            self.assertEqual(argv[argv.index("--network") + 1], "none")
            self.assertIn("--memory", argv)
            self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
