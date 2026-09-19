import hmac
import os
import tempfile
import threading
from typing import Optional

from anyio import to_thread
from fastapi import FastAPI, HTTPException, Query, Request

from content_utils import (
    PrintJob,
    UnsupportedContentError,
    coerce_bool,
    normalize_json_payload,
    normalize_raw_content,
    normalize_url,
)
from printer_utils import ThermalPrinter


app = FastAPI(
    title="Receipt Print Server",
    version="1.0.0",
    description="HTTP API for formatting and printing content to an ESC/POS thermal printer.",
)

_print_lock = threading.Lock()


def _require_api_key(request: Request):
    """Reject print requests without the configured key. No key configured means open access."""
    expected = os.environ.get("RECEIPT_API_KEY", "").strip()
    if not expected:
        return
    header = request.headers.get("authorization", "")
    supplied = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if not supplied:
        supplied = request.headers.get("x-api-key", "").strip()
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


@app.get("/")
def root():
    return {
        "service": "receipt-print-server",
        "endpoints": {
            "health": "GET /health",
            "print": "POST /print or POST /v1/print",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "printer_connection": os.environ.get("THERMAL_PRINTER_CONNECTION", "network"),
    }


@app.post("/print")
@app.post("/v1/print")
async def print_content(
    request: Request,
    print_type: Optional[str] = Query(None, alias="type"),
    cut: bool = Query(False),
    bold: bool = Query(False),
    dry_run: bool = Query(False),
):
    _require_api_key(request)
    try:
        job = await _job_from_request(request, requested_type=print_type, cut=cut, bold=bold)
    except UnsupportedContentError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if dry_run:
        return {"status": "dry_run", "job": job.response_summary()}

    try:
        await to_thread.run_sync(_execute_print_job, job)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Printer error: {exc}") from exc

    return {"status": "printed", "job": job.response_summary()}


async def _job_from_request(
    request: Request,
    requested_type: Optional[str],
    cut: bool,
    bold: bool,
) -> PrintJob:
    content_type = request.headers.get("content-type", "")
    mime_type = content_type.split(";", 1)[0].strip().lower()

    if mime_type == "multipart/form-data":
        return await _job_from_form(request, requested_type=requested_type, cut=cut, bold=bold)

    if mime_type == "application/json":
        payload = await request.json()
        return normalize_json_payload(payload, cut=cut, bold=bold, requested_type=requested_type)

    body = await request.body()
    return normalize_raw_content(
        body,
        content_type=content_type,
        requested_type=requested_type,
        cut=cut,
        bold=bold,
    )


async def _job_from_form(
    request: Request,
    requested_type: Optional[str],
    cut: bool,
    bold: bool,
) -> PrintJob:
    form = await request.form()
    form_type = form.get("type") or requested_type
    form_cut = coerce_bool(form.get("cut", cut))
    form_bold = coerce_bool(form.get("bold", bold))

    upload = form.get("file")
    if upload is not None and hasattr(upload, "read"):
        body = await upload.read()
        return normalize_raw_content(
            body,
            content_type=getattr(upload, "content_type", ""),
            requested_type=form_type,
            filename=getattr(upload, "filename", None),
            cut=form_cut,
            bold=form_bold,
            source="upload",
        )

    url = form.get("url")
    if url:
        return normalize_url(str(url), requested_type=form_type, cut=form_cut, bold=form_bold)

    content = form.get("content")
    if content is not None:
        return normalize_raw_content(
            str(content).encode("utf-8"),
            content_type=form.get("content_type") or "",
            requested_type=form_type,
            cut=form_cut,
            bold=form_bold,
            source="form",
        )

    raise UnsupportedContentError("Multipart requests must include file, url, or content")


def _execute_print_job(job: PrintJob):
    with _print_lock:
        printer = ThermalPrinter.from_env()
        try:
            if job.kind == "markdown":
                printer.print_markdown(str(job.content))
            elif job.kind == "text":
                printer.print_text(str(job.content), bold=job.bold)
            elif job.kind == "image":
                _print_image_bytes(printer, job)
            else:
                raise UnsupportedContentError(f"Unsupported print job kind {job.kind!r}")

            if job.cut:
                printer.cut_paper()
        finally:
            printer.close()


def _print_image_bytes(printer: ThermalPrinter, job: PrintJob):
    suffix = _suffix_for_mime(job.mime_type)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(job.content)
            temp_path = temp_file.name
        printer.print_image(temp_path)
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


def _suffix_for_mime(mime_type: str) -> str:
    suffixes = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }
    return suffixes.get(mime_type, ".img")


def main():
    import uvicorn

    host = os.environ.get("RECEIPT_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("RECEIPT_SERVER_PORT", "8080"))
    uvicorn.run("server:app", host=host, port=port)


if __name__ == "__main__":
    main()
