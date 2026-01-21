# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI tool and Python library for printing to an Epson TM-T88V thermal receipt printer over network (ESC/POS protocol). Supports text formatting, image dithering, markdown rendering, and bitmap output.

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
export THERMAL_PRINTER_IP=192.168.1.193
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
```

### Environment Variables

- `THERMAL_PRINTER_IP` - Printer IP address (default: 192.168.1.193)
- `THERMAL_PRINTER_PORT` - Printer port (default: 9100)

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
- Supports `--ip` and `--port` flags or env vars

**printer_utils.py** - `ThermalPrinter` class wrapping ESC/POS commands:
- Network connection to printer (default: 192.168.1.193:9100)
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
