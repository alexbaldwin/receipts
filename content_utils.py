from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from typing import Any, Optional, Union
from urllib.parse import unquote_to_bytes, urlparse
import base64
import binascii
import json
import re

from PIL import Image, UnidentifiedImageError
import requests


MARKDOWN_MIME_TYPES = {
    "text/markdown",
    "text/x-markdown",
    "application/markdown",
    "application/x-markdown",
}

TEXT_MIME_TYPES = {
    "text/plain",
    "application/xml",
    "text/xml",
    "application/yaml",
    "application/x-yaml",
}

JSON_MIME_TYPES = {
    "application/json",
    "application/ld+json",
}

TEXT_FILE_EXTENSIONS = {".txt", ".csv", ".log", ".tsv", ".yaml", ".yml", ".xml"}

REQUEST_TIMEOUT_SECONDS = 20


class UnsupportedContentError(ValueError):
    """Raised when the request body cannot be turned into printable content."""


@dataclass
class PrintJob:
    kind: str
    content: Union[str, bytes]
    mime_type: str = ""
    source: str = "body"
    filename: Optional[str] = None
    cut: bool = False
    bold: bool = False

    def response_summary(self):
        size = len(self.content) if isinstance(self.content, bytes) else len(self.content.encode("utf-8"))
        return {
            "kind": self.kind,
            "mime_type": self.mime_type,
            "source": self.source,
            "filename": self.filename,
            "bytes": size,
            "cut": self.cut,
            "bold": self.bold,
        }


class _ReceiptHTMLParser(HTMLParser):
    block_tags = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self._ensure_newline()
            self.parts.append("- ")
        elif tag in {"h1", "h2", "h3"}:
            self._ensure_newline()
            self.parts.append("#" * int(tag[1]))
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in self.block_tags:
            self._ensure_newline()

    def handle_data(self, data):
        if data:
            self.parts.append(data)

    def _ensure_newline(self):
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def text(self):
        text = "".join(self.parts)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def normalize_raw_content(
    body: bytes,
    content_type: Optional[str] = None,
    requested_type: Optional[str] = None,
    filename: Optional[str] = None,
    cut: bool = False,
    bold: bool = False,
    source: str = "body",
) -> PrintJob:
    if not body:
        raise UnsupportedContentError("No printable content was provided")

    mime_type = _mime_type(content_type)
    requested = _normalize_requested_type(requested_type)

    if requested == "image":
        _assert_image_bytes(body, mime_type)
        return PrintJob("image", body, mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    if requested == "markdown":
        return PrintJob("markdown", _decode_text(body), mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    if requested == "html":
        return PrintJob("markdown", html_to_markdownish_text(_decode_text(body)), mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    if requested == "text":
        return PrintJob("text", _decode_text(body), mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    if mime_type.startswith("image/") or _looks_like_image(body):
        return PrintJob("image", body, mime_type=mime_type or "image/*", source=source, filename=filename, cut=cut, bold=bold)

    if mime_type in MARKDOWN_MIME_TYPES or _filename_ext(filename) in {".md", ".markdown"}:
        return PrintJob("markdown", _decode_text(body), mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    if mime_type == "text/html" or _filename_ext(filename) in {".html", ".htm"}:
        return PrintJob("markdown", html_to_markdownish_text(_decode_text(body)), mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    if mime_type in JSON_MIME_TYPES or _filename_ext(filename) == ".json":
        return PrintJob("text", _pretty_json(body), mime_type=mime_type or "application/json", source=source, filename=filename, cut=cut, bold=bold)

    if (
        mime_type.startswith("text/")
        or mime_type in TEXT_MIME_TYPES
        or _filename_ext(filename) in TEXT_FILE_EXTENSIONS
        or _looks_like_text(body)
    ):
        return PrintJob("text", _decode_text(body), mime_type=mime_type, source=source, filename=filename, cut=cut, bold=bold)

    raise UnsupportedContentError(
        f"Unsupported content type {mime_type or 'unknown'}. "
        "Send text, markdown, HTML, JSON, or an image."
    )


def normalize_json_payload(
    payload: Any,
    cut: Optional[bool] = None,
    bold: Optional[bool] = None,
    requested_type: Optional[str] = None,
) -> PrintJob:
    if not isinstance(payload, dict):
        return PrintJob(
            "text",
            json.dumps(payload, indent=2, ensure_ascii=False),
            mime_type="application/json",
            cut=coerce_bool(cut),
            bold=coerce_bool(bold),
        )

    requested = _normalize_requested_type(requested_type or payload.get("type") or payload.get("format"))
    job_cut = coerce_bool(payload.get("cut", cut or False))
    job_bold = coerce_bool(payload.get("bold", bold or False))
    mime_type = payload.get("mime_type") or payload.get("content_type") or ""

    if payload.get("url"):
        return normalize_url(
            payload["url"],
            requested_type=requested,
            cut=job_cut,
            bold=job_bold,
        )

    content = _payload_content(payload)
    if requested is None:
        requested = _requested_type_from_payload_keys(payload)
    if content is None:
        return PrintJob(
            "text",
            json.dumps(payload, indent=2, ensure_ascii=False),
            mime_type="application/json",
            source="json",
            cut=job_cut,
            bold=job_bold,
        )

    if isinstance(content, str) and content.startswith("data:"):
        data_mime_type, data = decode_data_uri(content)
        return normalize_raw_content(
            data,
            content_type=mime_type or data_mime_type,
            requested_type=requested,
            cut=job_cut,
            bold=job_bold,
            source="json:data-uri",
        )

    if payload.get("encoding") == "base64":
        if not isinstance(content, str):
            raise UnsupportedContentError("Base64 content must be a string")
        data = _decode_base64(content)
        return normalize_raw_content(
            data,
            content_type=mime_type,
            requested_type=requested,
            cut=job_cut,
            bold=job_bold,
            source="json:base64",
        )

    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2, ensure_ascii=False)

    if isinstance(content, bytes):
        body = content
    else:
        body = str(content).encode("utf-8")

    return normalize_raw_content(
        body,
        content_type=mime_type,
        requested_type=requested,
        cut=job_cut,
        bold=job_bold,
        source="json",
    )


def normalize_url(url: str, requested_type: Optional[str] = None, cut: bool = False, bold: bool = False) -> PrintJob:
    url = str(url)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsupportedContentError("Only http and https URLs can be fetched")

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise UnsupportedContentError(f"Could not fetch URL: {exc}") from exc

    return normalize_raw_content(
        response.content,
        content_type=response.headers.get("content-type"),
        requested_type=requested_type,
        filename=parsed.path,
        cut=cut,
        bold=bold,
        source=url,
    )


def decode_data_uri(uri: str):
    match = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", uri, re.DOTALL)
    if not match:
        raise UnsupportedContentError("Invalid data URI")

    mime_type = match.group(1) or "text/plain"
    is_base64 = bool(match.group(2))
    payload = match.group(3)
    if is_base64:
        return mime_type, _decode_base64(payload)
    return mime_type, unquote_to_bytes(payload)


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def html_to_markdownish_text(html: str) -> str:
    parser = _ReceiptHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.text()


def _payload_content(payload):
    if "content" in payload:
        return payload["content"]
    if "markdown" in payload:
        return payload["markdown"]
    if "text" in payload:
        return payload["text"]
    if "image" in payload:
        return payload["image"]
    return None


def _requested_type_from_payload_keys(payload):
    if "markdown" in payload:
        return "markdown"
    if "text" in payload:
        return "text"
    if "image" in payload:
        return "image"
    return None


def _normalize_requested_type(value):
    if not value:
        return None
    value = str(value).strip().lower()
    aliases = {
        "auto": None,
        "md": "markdown",
        "markdown": "markdown",
        "text/markdown": "markdown",
        "plain": "text",
        "txt": "text",
        "text": "text",
        "text/plain": "text",
        "html": "html",
        "text/html": "html",
        "image": "image",
        "img": "image",
    }
    if value not in aliases:
        raise UnsupportedContentError(f"Unknown print type {value!r}")
    return aliases[value]


def _mime_type(content_type):
    if not content_type:
        return ""
    return content_type.split(";", 1)[0].strip().lower()


def _filename_ext(filename):
    if not filename or "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def _decode_text(body):
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def _pretty_json(body):
    try:
        parsed = json.loads(_decode_text(body))
    except json.JSONDecodeError:
        return _decode_text(body)
    return json.dumps(parsed, indent=2, ensure_ascii=False)


def _looks_like_image(body):
    try:
        with Image.open(BytesIO(body)) as image:
            image.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def _assert_image_bytes(body, mime_type):
    if _looks_like_image(body):
        return
    raise UnsupportedContentError(f"Content is not a valid image ({mime_type or 'unknown type'})")


def _looks_like_text(body):
    sample = body[:2048]
    if b"\x00" in sample:
        return False

    try:
        decoded = sample.decode("utf-8")
    except UnicodeDecodeError:
        return False

    if not decoded:
        return False

    good_chars = sum(1 for char in decoded if char.isprintable() or char in "\n\r\t")
    return (good_chars / max(len(decoded), 1)) > 0.85


def _decode_base64(value):
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise UnsupportedContentError("Base64 content is invalid") from exc
