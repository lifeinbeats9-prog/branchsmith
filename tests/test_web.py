import unittest
from unittest import mock

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


if __name__ == "__main__":
    unittest.main()
