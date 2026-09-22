import unittest
from unittest import mock

from branchsmith import web
from branchsmith.web import app


class WebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_is_public_demo_surface(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BranchSmith Live Demo", response.data)

    def test_healthz_is_stable(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertFalse(data["accepts_user_code"])

    def test_demo_requires_server_side_token_factory_configuration(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            response = self.client.post("/api/demo")
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.get_json()["error"])

    def test_demo_uses_current_python_interpreter_for_tests(self):
        fake_report = mock.Mock(winner_id="c1")
        fake_report.to_dict.return_value = {"winner_id": "c1"}
        web._cached_payload = None
        web._cached_at = 0.0
        with mock.patch.dict("os.environ", {"NEBIUS_API_KEY": "test-only"}), mock.patch(
            "branchsmith.web.NemotronPlanner"
        ), mock.patch("branchsmith.web.run_repair", return_value=fake_report) as run:
            response = self.client.post("/api/demo")
        self.assertEqual(response.status_code, 200)
        test_command = run.call_args.kwargs["test_command"]
        self.assertIn("-m unittest -q", test_command)
        self.assertIn(web.sys.executable, test_command)


if __name__ == "__main__":
    unittest.main()
