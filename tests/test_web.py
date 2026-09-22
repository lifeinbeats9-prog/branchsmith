import unittest
from unittest import mock

from branchsmith import web
from branchsmith.web import app


class WebTests(unittest.TestCase):
    def setUp(self):
        web._cached_payload = None
        web._cached_at = 0.0
        self.client = app.test_client()

    def test_index_is_public_demo_surface(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BranchSmith", response.data)
        self.assertIn(b"Multiple repair hypotheses", response.data)
        self.assertIn(b"Competing candidates", response.data)

    def test_healthz_is_stable(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)
        self.assertIn("public_repo", data)
        self.assertFalse(data["accepts_user_code"])

    def test_demo_requires_server_side_token_factory_configuration(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            response = self.client.post("/api/demo")
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.get_json()["error"])

    def test_demo_uses_current_python_interpreter_and_emits_evidence_metadata(self):
        fake_report = mock.Mock(winner_id="c1")
        fake_report.to_dict.return_value = {
            "winner_id": "c1",
            "planner": "planner",
            "sandbox": "sandbox",
            "baseline": {"passed": False, "exit_code": 1},
            "candidates": [
                {"candidate": {"candidate_id": "c1", "edits": []}, "test": {"exit_code": 0}, "passed": True, "edit_count": 1},
                {"candidate": {"candidate_id": "c2", "edits": []}, "test": {"exit_code": 1}, "passed": False, "edit_count": 1},
            ],
        }
        with mock.patch.dict("os.environ", {"NEBIUS_API_KEY": "test-only"}), mock.patch(
            "branchsmith.web.NemotronPlanner"
        ), mock.patch("branchsmith.web.run_repair", return_value=fake_report) as run:
            response = self.client.post("/api/demo")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["evidence"]["candidate_count"], 2)
        self.assertEqual(data["evidence"]["pass_count"], 1)
        self.assertEqual(data["report"]["winner_id"], "c1")
        self.assertFalse(data["cached"])
        self.assertTrue(data["run_id"])
        self.assertGreaterEqual(data["elapsed_ms"], 0)
        test_command = run.call_args.kwargs["test_command"]
        self.assertIn("-m unittest -q", test_command)
        self.assertIn(web.sys.executable, test_command)

    def test_second_demo_request_uses_short_cache(self):
        fake_report = mock.Mock(winner_id="c1")
        fake_report.to_dict.return_value = {
            "winner_id": "c1",
            "planner": "planner",
            "sandbox": "sandbox",
            "baseline": {"passed": False, "exit_code": 1},
            "candidates": [],
        }
        with mock.patch.dict("os.environ", {"NEBIUS_API_KEY": "test-only"}), mock.patch(
            "branchsmith.web.NemotronPlanner"
        ), mock.patch("branchsmith.web.run_repair", return_value=fake_report) as run:
            first = self.client.post("/api/demo")
            second = self.client.post("/api/demo")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(run.call_count, 1)
        self.assertFalse(first.get_json()["cached"])
        self.assertTrue(second.get_json()["cached"])


if __name__ == "__main__":
    unittest.main()
