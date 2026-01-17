"""
Markdown printing example.

Renders markdown with headers, lists, bold text, and inline images.
See markdown/input.md for the source document format.
"""
from printer_utils import ThermalPrinter

printer = ThermalPrinter()

# Read markdown content from file
with open('markdown/input.md', 'r') as f:
    markdown_text = f.read()

printer.print_markdown(markdown_text)
printer.cut_paper() 