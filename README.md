# Thermal Printer

Python library for printing to Epson TM-T88V thermal receipt printers over the network. Supports text formatting, image dithering, markdown rendering, and more.

## Features

- **Text printing** with bold, italic, underline, and various text sizes
- **Image printing** with ordered dithering (Bayer matrix) for high-quality output
- **Markdown rendering** with headers, lists, bold text, and inline images
- **Multiple dithering algorithms**: Bayer 32x32, Clustered Dot, Variable 2x2
- **Remote image support**: Print images directly from URLs

## Requirements

- Python 3.10+
- Epson TM-T88V (or compatible ESC/POS printer)
- Network connection to printer

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd printer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from printer_utils import ThermalPrinter

# Connect to printer (default: 192.168.1.193:9100)
printer = ThermalPrinter()

# Print text
printer.print_text("Hello, World!", bold=True)

# Print an image
printer.print_image("photo.jpg")

# Cut the paper
printer.cut_paper()
```

## Examples

### Basic Image Printing

`print_example.py` - Print a header and image:

```python
from printer_utils import ThermalPrinter

printer = ThermalPrinter()
printer.print_text("=== Image Test ===", bold=True)
printer.print_image("cover.jpg")
printer.cut_paper()
```

### Markdown Documents

`markdown_example.py` - Print formatted markdown with embedded images:

```python
from printer_utils import ThermalPrinter

printer = ThermalPrinter()

with open('markdown/input.md', 'r') as f:
    markdown_text = f.read()

printer.print_markdown(markdown_text)
printer.cut_paper()
```

Supported markdown features:
- Headers (h1, h2, h3+)
- Bullet lists (`-`, `*`, `+`)
- Numbered lists
- Bold text (`**text**`)
- Inline images (`![alt](path.jpg)`)

### Dithering Comparison

`dither_example.py` - Compare different dithering algorithms:

```python
from printer_utils import ThermalPrinter
from image_utils import ImageDitherer, DitherMethod

printer = ThermalPrinter()
ditherer = ImageDitherer()

# Available methods: BAYER_32x32, CLUSTERED_DOT_6, VARIABLE_2x2
dithered = ditherer.dither_image("photo.jpg", DitherMethod.BAYER_32x32)
dithered.save("output.png")
```

### Typography Showcase

`typography_example.py` - Demonstrate all text formatting options:

- Normal, bold, italic, underline text
- Double-strike and reverse (white on black)
- Text sizes: normal, double width, double height, triple
- Combined effects (bold + italic, etc.)

### ASCII Art / Bitmap

`ascii_example.py` - Print images as 1-bit bitmaps with contrast enhancement.

## API Reference

### ThermalPrinter

```python
ThermalPrinter(ip_address="192.168.1.193", port=9100)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `print_text(text, bold=False)` | Print text with optional bold |
| `print_image(path_or_url)` | Print image (local file or URL) with dithering |
| `print_markdown(text)` | Parse and print markdown-formatted text |
| `print_ascii_art(path, width=512)` | Print image as high-contrast bitmap |
| `cut_paper()` | Cut the paper |

### ImageDitherer

```python
ImageDitherer()
```

**Methods:**

| Method | Description |
|--------|-------------|
| `dither_image(path_or_image, method)` | Apply dithering algorithm to image |

**DitherMethod enum:**
- `BAYER_32x32` - Large Bayer matrix, smooth gradients
- `CLUSTERED_DOT_6` - Clustered dot pattern
- `VARIABLE_2x2` - Small matrix, higher contrast

## Printer Setup

1. Connect the TM-T88V to your network
2. Find the printer's IP address (check printer settings or router DHCP)
3. Default port is 9100 (standard raw printing port)
4. Update the IP in your code or use the default

```python
# Custom IP address
printer = ThermalPrinter(ip_address="192.168.1.100", port=9100)
```

## Printer Specs (TM-T88V)

- Max width: 512 pixels
- DPI: 180
- Characters per line: ~42 (Font A)

## License

MIT
