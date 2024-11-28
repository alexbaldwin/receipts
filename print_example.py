from printer_utils import ThermalPrinter

# Initialize printer
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