from printer_utils import ThermalPrinter

# Initialize printer
printer = ThermalPrinter()

# Print local image
printer.print_image("cover.jpg")

# Print remote image
printer.print_image("https://example.com/image.jpg")

printer.cut_paper() 