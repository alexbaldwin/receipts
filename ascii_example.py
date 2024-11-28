from printer_utils import ThermalPrinter

# Initialize printer
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