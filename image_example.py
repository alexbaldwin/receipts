"""
Image printing example demonstrating local and remote image support.

The print_image() method accepts both local file paths and HTTP/HTTPS URLs.
"""
from printer_utils import ThermalPrinter

printer = ThermalPrinter()

# Print local image
printer.print_image("cover.jpg")

# Print remote image (supports any HTTP/HTTPS URL)
# printer.print_image("https://example.com/image.jpg")

printer.cut_paper() 