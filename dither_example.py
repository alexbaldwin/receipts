from printer_utils import ThermalPrinter
from image_utils import ImageDitherer, DitherMethod
import os

def main():
    # Initialize printer and ditherer
    printer = ThermalPrinter()
    ditherer = ImageDitherer()
    
    # Input image path - replace with your image path
    input_image = "cover.jpg"
    
    # Print header
    printer.print_text("Dithering Examples", bold=True)
    printer.print_text("-----------------\n")
    
    # Print original image
    printer.print_text("Original:", bold=True)
    printer.print_image(input_image)
    printer.print_text("\n")
    
    # Print Bayer 32x32 dithered version
    printer.print_text("Bayer 32x32:", bold=True)
    dithered = ditherer.dither_image(input_image, DitherMethod.BAYER_32x32)
    printer.print_image(dithered)
    printer.print_text("\n")
    
    # Print Clustered Dot v6 dithered version
    printer.print_text("Clustered Dot v6:", bold=True)
    dithered = ditherer.dither_image(input_image, DitherMethod.CLUSTERED_DOT_6)
    printer.print_image(dithered)
    printer.print_text("\n")
    
    # Print Variable 2x2 dithered version
    printer.print_text("Variable 2x2:", bold=True)
    dithered = ditherer.dither_image(input_image, DitherMethod.VARIABLE_2x2)
    printer.print_image(dithered)
    printer.print_text("\n")

if __name__ == "__main__":
    main() 