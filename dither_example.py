"""
Dithering comparison example.

Prints the same image using different dithering algorithms side by side
to compare their visual characteristics:
- BAYER_32x32: Smooth gradients, crosshatch pattern
- CLUSTERED_DOT_6: Halftone-like clustered dots
- VARIABLE_2x2: High contrast, smaller pattern
"""
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
    printer.print_text("Dithering Examples\n", bold=True)
    printer.print_text("-----------------\n")
    
    # Print original image
    printer.print_text("Original:\n", bold=True)
    printer.print_image(input_image)
    printer.print_text("\n")
    
    # Print each dither method
    methods = [
        (DitherMethod.BAYER_32x32, "Bayer 32x32"),
        (DitherMethod.CLUSTERED_DOT_6, "Clustered Dot v6"),
        (DitherMethod.VARIABLE_2x2, "Variable 2x2")
    ]
    
    for method, label in methods:
        printer.print_text(f"{label}:\n", bold=True)
        # Dither the image
        dithered = ditherer.dither_image(input_image, method)
        # Save temporarily and print
        temp_path = f"temp_{method.value}.png"
        dithered.save(temp_path)
        printer.print_image(temp_path)
        printer.print_text("\n")
        # Clean up temporary file
        os.remove(temp_path)
    
    # Cut the paper
    printer.cut_paper()

if __name__ == "__main__":
    main() 