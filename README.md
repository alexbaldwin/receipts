# Thermal Receipt Printer

CLI tool and Python library for printing to Epson TM-T88V thermal receipt printers over the network. Supports text formatting, image dithering, markdown rendering, and more.

## Features

- **CLI tool** - `receipt` command for terminal usage
- **Markdown printing** with headers, lists, bold text, and inline images
- **Image printing** with Bayer matrix dithering
- **Remote image support** - Print images from URLs
- **HTTP print server** - Run on a Raspberry Pi and accept JSON, raw bodies, URLs, or file uploads
- **Network or USB printer connection** - Configure with environment variables
- **Environment variable config** - Set printer IP once, use everywhere

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or run directly without installing
uv run receipt print "# Hello"
uv run receipt-server

# Using pip
pip install -e .
```

After installation, the `receipt` command is available globally.

## CLI Usage

### Configuration

Set your printer IP via environment variable (recommended):

```bash
export THERMAL_PRINTER_IP=192.168.2.2
export THERMAL_PRINTER_PORT=9100  # optional, default is 9100
```

For USB-connected printers:

```bash
export THERMAL_PRINTER_CONNECTION=usb
export THERMAL_PRINTER_USB_VENDOR_ID=0x04b8
export THERMAL_PRINTER_USB_PRODUCT_ID=0x0202
```

Or pass it with each command:

```bash
receipt --ip 192.168.2.2 print "# Hello"
```

### Commands

#### Print Markdown

```bash
# Print a markdown file
receipt print /path/to/document.md

# Print a markdown string (use single quotes)
receipt print '# Hello World\n\nThis is **bold** text.'

# Print from stdin
echo '# Hello' | receipt print -

# Cut paper after printing
receipt print --cut '# Receipt\n\nThank you'
```

#### Print Plain Text

```bash
receipt text "Hello World"
receipt text --bold "IMPORTANT"
receipt text --cut "Done!"
```

#### Print Image

```bash
# Local file
receipt image photo.jpg

# URL
receipt image "https://example.com/logo.png"

# With paper cut
receipt image --cut logo.png
```

#### Cut Paper

```bash
receipt cut
```

## HTTP Server

Start the server:

```bash
receipt-server
```

By default it listens on `0.0.0.0:8080`. Change that with:

```bash
export RECEIPT_SERVER_HOST=0.0.0.0
export RECEIPT_SERVER_PORT=8080
```

### Print Requests

Raw markdown:

```bash
curl -X POST 'http://raspberrypi.local:8080/print?cut=true' \
  -H 'content-type: text/markdown' \
  --data-binary '# Hello\n\nPrinted from the Pi server.'
```

JSON:

```bash
curl -X POST 'http://raspberrypi.local:8080/v1/print' \
  -H 'content-type: application/json' \
  -d '{"markdown":"# Receipt\n\n**Total:** $7.50","cut":true}'
```

Image upload:

```bash
curl -X POST 'http://raspberrypi.local:8080/print?cut=true' \
  -F 'file=@logo.png'
```

URL fetch:

```bash
curl -X POST 'http://raspberrypi.local:8080/print' \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com/logo.png","cut":true}'
```

Dry-run without printing:

```bash
curl -X POST 'http://raspberrypi.local:8080/print?dry_run=true' \
  -H 'content-type: text/plain' \
  --data-binary 'hello'
```

Supported inputs:

- `text/markdown`, `text/plain`, `text/html`, and JSON bodies
- `image/*` bodies and multipart file uploads
- JSON `content`, `markdown`, `text`, `image`, or `url` fields
- Base64/data URI images via JSON `content`

Unknown binary content returns `415 Unsupported Media Type` instead of sending junk to the printer.

### Markdown Support

The `print` command supports:

- Headers: `# H1`, `## H2`, `### H3`
- Bold: `**text**` or `__text__`
- Bullet lists: `- item`, `* item`, `+ item`
- Numbered lists: `1. item`
- Images: `![alt text](path_or_url)`

### Examples

```bash
# Simple receipt (use single quotes to avoid shell issues)
receipt print '# Order #1234\n\n- Coffee: $4.50\n- Muffin: $3.00\n\n**Total: $7.50**'

# With logo from URL
receipt print '![Logo](https://example.com/logo.png)\n\n# Welcome\n\nThank you for visiting'

# From a file
receipt print receipt.md --cut
```

---

## LLM Integration Guide

This section documents how to call the `receipt` CLI from an LLM or automated system.

### Environment Setup

Before calling, ensure the printer IP is configured:

```bash
export THERMAL_PRINTER_IP=192.168.2.2
```

### Command Patterns

#### 1. Print Simple Markdown String (Use Single Quotes)

```bash
receipt print '# Title\n\nBody text with **bold**.'
```

#### 2. Print Markdown File (Absolute Paths)

```bash
receipt print /absolute/path/to/document.md
```

#### 3. Print with Inline Image URLs

```bash
receipt print '# Order\n\n![Logo](https://example.com/logo.png)\n\nThank you'
```

#### 4. Print and Cut

```bash
receipt print --cut '# Receipt\n\nDone'
```

### Shell Escaping (Important)

**Always use single quotes** for markdown strings to avoid shell interpretation issues:

```bash
# Correct - single quotes
uv run receipt print '# Hello\n\n**Bold text**'

# Wrong - double quotes cause issues with ** ! $ etc
uv run receipt print "# Hello\n\n**Bold**"  # zsh: no matches found
```

The CLI converts `\n` to newlines internally, so single quotes work correctly.

| Character | In Single Quotes | Notes |
|-----------|------------------|-------|
| `\n` | Works | CLI converts to newline |
| `**` | Works | No glob expansion |
| `!` | Works | No history expansion |
| `$` | Works | No variable expansion |

### Multi-line Content (Bash Heredoc)

For complex content, use a heredoc:

```bash
receipt print <<'EOF'
# Receipt

| Item | Price |
|------|-------|
| Coffee | $4.50 |
| Muffin | $3.00 |

**Total: $7.50**

Thank you for your purchase!
EOF
```

### Structured Receipt Example

```bash
receipt print --cut '# Store Name\n\n## Order #12345\n\n- Item 1: $10.00\n- Item 2: $15.00\n- Item 3: $5.00\n\n---\n\n**Subtotal: $30.00**\n**Tax: $2.40**\n**Total: $32.40**\n\n![QR Code](https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ORDER12345)\n\nThank you for shopping'
```

### Error Handling

The CLI exits with:
- `0` on success
- `1` on error (connection failed, file not found, etc.)

Errors are printed to stderr:

```bash
receipt print "test" 2>/dev/null  # Suppress errors
```

### Checking Printer Connectivity

```bash
# Simple test
receipt print "test" && echo "Printer OK"
```

---

## Python API

For programmatic use, import directly:

```python
from printer_utils import ThermalPrinter

# Connect to printer
printer = ThermalPrinter(ip_address="192.168.2.2", port=9100)

# Print text
printer.print_text("Hello, World!", bold=True)

# Print markdown
printer.print_markdown("# Hello\n\nThis is **bold**.")

# Print image (local or URL)
printer.print_image("photo.jpg")
printer.print_image("https://example.com/logo.png")

# Cut paper
printer.cut_paper()
```

### ImageDitherer

For custom dithering:

```python
from image_utils import ImageDitherer, DitherMethod

ditherer = ImageDitherer()

# Available methods: BAYER_32x32, CLUSTERED_DOT_6, VARIABLE_2x2
dithered = ditherer.dither_image("photo.jpg", DitherMethod.BAYER_32x32)
dithered.save("output.png")
```

## Printer Setup

### Network

1. Connect the TM-T88V to Ethernet or Wi-Fi.
2. Find the printer's IP address from its settings page or your router DHCP table.
3. Set `THERMAL_PRINTER_CONNECTION=network`.
4. Set `THERMAL_PRINTER_IP` and optionally `THERMAL_PRINTER_PORT`.

### USB

1. Connect the printer to the Raspberry Pi over USB.
2. Run `lsusb` and find the `vendor:product` pair, for example `04b8:0202`.
3. Set `THERMAL_PRINTER_CONNECTION=usb`.
4. Set `THERMAL_PRINTER_USB_VENDOR_ID=0x04b8` and `THERMAL_PRINTER_USB_PRODUCT_ID=0x0202`.
5. Make sure the service user can access USB printers, usually by adding it to the `lp` group.

## Raspberry Pi Service

Example deployment files live in `deploy/`.

```bash
sudo apt update
sudo apt install -y git python3-venv

git clone <this-repo-url> /home/pi/receipts
cd /home/pi/receipts
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

sudo mkdir -p /etc/receipt-printer
sudo cp deploy/receipt-server.env.example /etc/receipt-printer/server.env
sudo cp deploy/receipt-server.service /etc/systemd/system/receipt-server.service
sudo systemctl daemon-reload
sudo systemctl enable --now receipt-server
```

Edit `/etc/receipt-printer/server.env` for your printer connection. If your Pi user or checkout path is not `pi` and `/home/pi/receipts`, edit `/etc/systemd/system/receipt-server.service` before enabling it.

Check status and logs:

```bash
systemctl status receipt-server
journalctl -u receipt-server -f
```

## Printer Specs (TM-T88V)

- Max width: 512 pixels
- DPI: 180
- Characters per line: ~42 (Font A)

## License

MIT
