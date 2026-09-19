import asyncio
import unittest

from content_utils import UnsupportedContentError
from server import _job_from_request


class FakeRequest:
    def __init__(self, headers=None, body=b"", json_payload=None, form_payload=None):
        self.headers = headers or {}
        self._body = body
        self._json_payload = json_payload
        self._form_payload = form_payload or {}

    async def body(self):
        return self._body

    async def json(self):
        return self._json_payload

    async def form(self):
        return self._form_payload


class ServerTests(unittest.TestCase):
    def test_raw_markdown_dry_run(self):
        job = asyncio.run(
            _job_from_request(
                FakeRequest(headers={"content-type": "text/markdown"}, body=b"# Hello"),
                requested_type=None,
                cut=False,
                bold=False,
            )
        )

        self.assertEqual(job.kind, "markdown")

    def test_json_text_dry_run_with_options(self):
        job = asyncio.run(
            _job_from_request(
                FakeRequest(
                    headers={"content-type": "application/json"},
                    json_payload={"text": "Hello", "bold": True, "cut": True},
                ),
                requested_type=None,
                cut=False,
                bold=False,
            )
        )

        self.assertEqual(job.kind, "text")
        self.assertTrue(job.bold)
        self.assertTrue(job.cut)

    def test_rejects_unknown_binary(self):
        with self.assertRaises(UnsupportedContentError):
            asyncio.run(
                _job_from_request(
                    FakeRequest(headers={"content-type": "application/octet-stream"}, body=b"\x00\x01\x02"),
                    requested_type=None,
                    cut=False,
                    bold=False,
                )
            )


class ApiKeyTests(unittest.TestCase):
    def test_print_requires_api_key_when_configured(self):
        from unittest import mock
        from fastapi.testclient import TestClient
        from server import app

        with mock.patch.dict("os.environ", {"RECEIPT_API_KEY": "secret"}):
            client = TestClient(app)
            headers = {"Content-Type": "text/plain"}
            denied = client.post("/print?dry_run=true", content="hi", headers=headers)
            self.assertEqual(denied.status_code, 401)
            allowed = client.post(
                "/print?dry_run=true", content="hi", headers={**headers, "Authorization": "Bearer secret"}
            )
            self.assertEqual(allowed.status_code, 200)
            via_header = client.post(
                "/print?dry_run=true", content="hi", headers={**headers, "X-API-Key": "secret"}
            )
            self.assertEqual(via_header.status_code, 200)


if __name__ == "__main__":
    unittest.main()
