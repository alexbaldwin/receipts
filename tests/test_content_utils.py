import base64
import unittest
from io import BytesIO

from PIL import Image

from content_utils import UnsupportedContentError, normalize_json_payload, normalize_raw_content


def png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (2, 2), "white").save(buffer, format="PNG")
    return buffer.getvalue()


class ContentUtilsTests(unittest.TestCase):
    def test_markdown_content_type(self):
        job = normalize_raw_content(b"# Hello\n\n**Pi**", content_type="text/markdown")

        self.assertEqual(job.kind, "markdown")
        self.assertIn("# Hello", job.content)

    def test_json_markdown_shortcut_sets_type(self):
        job = normalize_json_payload({"markdown": "# Hello", "cut": "true"})

        self.assertEqual(job.kind, "markdown")
        self.assertTrue(job.cut)

    def test_html_becomes_markdownish_text(self):
        job = normalize_raw_content(b"<h1>Hello</h1><p>World</p>", content_type="text/html")

        self.assertEqual(job.kind, "markdown")
        self.assertIn("# Hello", job.content)
        self.assertIn("World", job.content)

    def test_image_detection_from_octet_stream(self):
        job = normalize_raw_content(png_bytes(), content_type="application/octet-stream")

        self.assertEqual(job.kind, "image")

    def test_data_uri_payload(self):
        encoded = base64.b64encode(png_bytes()).decode("ascii")
        job = normalize_json_payload({"content": f"data:image/png;base64,{encoded}"})

        self.assertEqual(job.kind, "image")
        self.assertGreater(len(job.content), 0)

    def test_unknown_binary_rejected(self):
        with self.assertRaises(UnsupportedContentError):
            normalize_raw_content(b"\x00\x01\x02", content_type="application/octet-stream")

    def test_non_utf8_octet_stream_rejected(self):
        with self.assertRaises(UnsupportedContentError):
            normalize_raw_content(b"\xff\xfe\xfd\xfc", content_type="application/octet-stream")

    def test_invalid_base64_rejected(self):
        with self.assertRaises(UnsupportedContentError):
            normalize_json_payload({"content": "not base64!", "encoding": "base64"})


if __name__ == "__main__":
    unittest.main()
