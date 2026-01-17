"""
Bitmap printing example.

Prints an image as a high-contrast 1-bit bitmap. The image is converted
to grayscale, contrast-enhanced, inverted, and printed at full width.

Note: Despite the name, this doesn't output ASCII characters - it prints
a binary (black/white) raster image.
"""
from printer_utils import ThermalPrinter

printer = ThermalPrinter()

# Print a title
printer.print_text("=== Image to Bitmap Test ===", bold=True)
printer.print_text("\n")

# Print the image using full printer width
printer.print_ascii_art(
    "cover.jpg",
    width=512  # Use full printer width
)

# Add some spacing
printer.print_text("\n")

# Cut the paper
printer.cut_paper() 