"""
Basic image printing example.

Prints a header followed by an image using the default Bayer dithering.
"""
from printer_utils import ThermalPrinter

printer = ThermalPrinter()

# Print a header
printer.print_text("=== Image Test ===", bold=True)
printer.print_text("\n")

# Print the image
printer.print_image("cover.jpg")

# Add some spacing
printer.print_text("\n")

# Cut the paper
printer.cut_paper() 