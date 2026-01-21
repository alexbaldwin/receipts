# Thermal Receipt Printer

CLI tool and Python library for printing to Epson TM-T88V thermal receipt printers over the network. Supports text formatting, image dithering, markdown rendering, and more.

## Features

- **CLI tool** - `receipt` command for terminal usage
- **Markdown printing** with headers, lists, bold text, and inline images
- **Image printing** with Bayer matrix dithering
- **Remote image support** - Print images from URLs
- **Environment variable config** - Set printer IP once, use everywhere

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or run directly without installing
uv run receipt print "# Hello"

# Using pip
pip install -e .
```

After installation, the `receipt` command is available globally.

## CLI Usage

### Configuration

Set your printer IP via environment variable (recommended):

```bash
export THERMAL_PRINTER_IP=192.168.1.193
export THERMAL_PRINTER_PORT=9100  # optional, default is 9100
```

Or pass it with each command:

```bash
receipt --ip 192.168.1.193 print "# Hello"
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
export THERMAL_PRINTER_IP=192.168.1.193
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
printer = ThermalPrinter(ip_address="192.168.1.193", port=9100)

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

1. Connect the TM-T88V to your network
2. Find the printer's IP address (check printer settings or router DHCP)
3. Default port is 9100 (standard raw printing port)
4. Set `THERMAL_PRINTER_IP` environment variable

## Printer Specs (TM-T88V)

- Max width: 512 pixels
- DPI: 180
- Characters per line: ~42 (Font A)

## License

MIT
