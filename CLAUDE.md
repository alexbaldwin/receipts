# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool, HTTP server, and Python library for printing to an Epson TM-T88V thermal receipt printer over network or USB (ESC/POS protocol). Supports text formatting, image dithering, markdown rendering, and bitmap output.

## Setup

```bash
# Using uv (recommended)
uv pip install -e .

# Or run directly without installing
uv run receipt print "# Hello"

# Using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## CLI Usage

The `receipt` command is the primary interface. Configure printer IP via environment variable:

```bash
export THERMAL_PRINTER_IP=192.168.2.2
```

### Commands

**Always use single quotes** for markdown strings (avoids zsh issues with `**`, `!`, `$`):

```bash
receipt print '# Hello\n\nMarkdown with **bold**'  # Print markdown string
receipt print /path/to/file.md                      # Print markdown file
receipt print --cut '# Receipt'                     # Print and cut paper
receipt text 'Plain text'                           # Print plain text
receipt text --bold 'Bold text'                     # Print bold text
receipt image photo.jpg                             # Print image (local)
receipt image 'https://example.com/img.png'        # Print image (URL)
receipt cut                                         # Cut paper only
receipt-server                                      # Start HTTP server on 0.0.0.0:8080
```

### Environment Variables

- `THERMAL_PRINTER_IP` - Printer IP address (default: 192.168.2.2)
- `THERMAL_PRINTER_PORT` - Printer port (default: 9100)
- `THERMAL_PRINTER_CONNECTION` - `network` or `usb` (default: network)
- `THERMAL_PRINTER_USB_VENDOR_ID` / `THERMAL_PRINTER_USB_PRODUCT_ID` - USB IDs from `lsusb`
- `RECEIPT_SERVER_HOST` / `RECEIPT_SERVER_PORT` - HTTP server bind config

## Running Examples

```bash
source .venv/bin/activate

python print_example.py      # Basic image with header
python image_example.py      # Local/remote image demo
python markdown_example.py   # Markdown with embedded images
python dither_example.py     # Compare dithering algorithms
python typography_example.py # Text formatting showcase
python ascii_example.py      # High-contrast bitmap output
```

## Architecture

### Core Modules

**cli.py** - CLI entry point using argparse:
- Subcommands: `print`, `text`, `image`, `cut`
- Reads from file paths, strings, or stdin
- Supports network and USB printer config flags or env vars

**server.py** - FastAPI HTTP server:
- `POST /print` and `POST /v1/print` accept JSON, raw bodies, multipart uploads, or URLs
- `dry_run=true` validates request normalization without touching printer hardware
- Serializes print jobs with a process lock so concurrent requests do not interleave printer bytes

**content_utils.py** - Content normalization:
- Detects markdown, text, HTML, JSON, image bytes, data URIs, and URLs
- Produces `PrintJob` objects with `markdown`, `text`, or `image` kind
- Rejects unsupported binary bodies before they reach the printer

**printer_utils.py** - `ThermalPrinter` class wrapping ESC/POS commands:
- Network connection to printer (default: 192.168.2.2:9100) or USB connection via vendor/product ID
- `print_text()` - Basic text with bold support
- `print_image()` - Image printing with Bayer matrix dithering (local files or URLs)
- `print_markdown()` - Markdown rendering with headers, lists, bold, and inline images
- `print_ascii_art()` - 1-bit bitmap output
- `cut_paper()` - Paper cutting command

**image_utils.py** - `ImageDitherer` class for image processing:
- `DitherMethod` enum: BAYER_32x32, CLUSTERED_DOT_6, VARIABLE_2x2
- `dither_image()` - Apply dithering to PIL Image or file path

### Printer Constants (TM-T88V)

- MAX_WIDTH: 512 pixels
- DPI: 180
- CHARS_PER_LINE: 42

### ESC/POS Commands Used

Typography effects are controlled via raw ESC/POS commands (see typography_example.py):
- Bold: `\x1B\x45\x01/\x00`
- Italic: `\x1B\x34\x01/\x00`
- Underline: `\x1B\x2D\x01/\x00`
- Text sizing: `\x1D\x21\xNN`
- Reverse print: `\x1D\x42\x01/\x00`

### libdither

Reference C library for dithering algorithms (not used by Python code). Contains documentation and examples of many dithering techniques.

## Raspberry Pi deployment

See `deploy/README.md`. `deploy/install.sh` sets up the venv, udev rule, env file, and systemd unit.
USB needs `python-escpos[usb]` (pyusb). Every job must call `ThermalPrinter.close()` (or use it as a
context manager) so the USB interface is released before the next job, or the next open fails with
"Resource busy". The TM-T88V ignores its built-in USB port when an interface card is fitted until
"Built-in USB" is selected with the FEED button menu (steps in the deploy README).
