"""
Typography showcase example.

Demonstrates all available text formatting options on the TM-T88V:
- Text effects: bold, italic, underline, double-strike, reverse
- Text sizes: normal, double width/height, triple
- Combinations of effects

Uses raw ESC/POS commands for full control over formatting.
"""
from printer_utils import ThermalPrinter

def print_typography_samples():
    printer = ThermalPrinter()
    
    # Reset printer to default state
    printer._raw(b'\x1B\x40')  # Initialize command
    
    # Set Font B for entire output
    printer._raw(b'\x1B\x4D\x01')  # Select Font B
    
    # Print title
    printer._raw(b'\x1b\x21\x30')  # Double width + Double height
    printer.print_text("Typography Samples\n\n")
    printer._raw(b'\x1b\x21\x00')  # Reset text size
    
    # Remove Font Selection section and start with Text Effects
    printer.print_text("=== Text Effects ===\n")
    
    # Normal text
    printer.print_text("Normal: The quick brown fox\n")
    
    # Bold/Emphasis text
    printer._raw(b'\x1B\x45\x01')  # Enable emphasis
    printer.print_text("Bold: The quick brown fox\n")
    printer._raw(b'\x1B\x45\x00')  # Disable emphasis
    
    # Italic text
    printer._raw(b'\x1B\x34\x01')  # Enable italics
    printer.print_text("Italic: The quick brown fox\n")
    printer._raw(b'\x1B\x34\x00')  # Disable italics
    
    # Underline text (1-dot thickness)
    printer._raw(b'\x1B\x2D\x01')  # Enable underline
    printer.print_text("Underline: The quick brown fox\n")
    printer._raw(b'\x1B\x2D\x00')  # Disable underline
    
    # Underline text (2-dot thickness)
    printer._raw(b'\x1B\x2D\x02')  # Enable thick underline
    printer.print_text("Thick Underline: The quick brown fox\n")
    printer._raw(b'\x1B\x2D\x00')  # Disable underline
    
    # Double-strike
    printer._raw(b'\x1B\x47\x01')  # Enable double-strike
    printer.print_text("Double-strike: The quick brown fox\n")
    printer._raw(b'\x1B\x47\x00')  # Disable double-strike
    
    # Reverse print (white on black)
    printer._raw(b'\x1D\x42\x01')  # Enable reverse print
    printer.print_text("Reverse: The quick brown fox\n")
    printer._raw(b'\x1D\x42\x00')  # Disable reverse print
    printer.print_text("\n")
    
    # Text Size Examples
    printer.print_text("=== Text Sizes ===\n")
    
    # Normal size
    printer._raw(b'\x1D\x21\x00')  # Normal size
    printer.print_text("Normal size text\n")
    
    # Double width
    printer._raw(b'\x1D\x21\x10')  # Double width
    printer.print_text("Double width\n")
    
    # Double height
    printer._raw(b'\x1D\x21\x01')  # Double height
    printer.print_text("Double height\n")
    
    # Double width + height
    printer._raw(b'\x1D\x21\x11')  # Double width + height
    printer.print_text("Double both\n")
    
    # Triple width + height
    printer._raw(b'\x1D\x21\x22')  # Triple width + height
    printer.print_text("Triple both\n")
    
    # Reset to normal
    printer._raw(b'\x1D\x21\x00')
    
    # Combinations
    printer.print_text("\n=== Combinations ===\n")
    
    # Bold + Italic
    printer._raw(b'\x1B\x45\x01')  # Enable bold
    printer._raw(b'\x1B\x34\x01')  # Enable italic
    printer.print_text("Bold + Italic\n")
    printer._raw(b'\x1B\x45\x00')  # Disable bold
    printer._raw(b'\x1B\x34\x00')  # Disable italic
    
    # Bold + Underline
    printer._raw(b'\x1B\x45\x01')  # Enable bold
    printer._raw(b'\x1B\x2D\x01')  # Enable underline
    printer.print_text("Bold + Underline\n")
    printer._raw(b'\x1B\x45\x00')  # Disable bold
    printer._raw(b'\x1B\x2D\x00')  # Disable underline
    
    # Double size + Bold
    printer._raw(b'\x1D\x21\x11')  # Double size
    printer._raw(b'\x1B\x45\x01')  # Enable bold
    printer.print_text("Double + Bold\n")
    printer._raw(b'\x1D\x21\x00')  # Normal size
    printer._raw(b'\x1B\x45\x00')  # Disable bold
    
    # Final spacing and cut
    printer.print_text("\n\n")
    printer.cut_paper()

if __name__ == "__main__":
    print_typography_samples() 