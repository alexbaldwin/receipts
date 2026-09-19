#!/usr/bin/env python3
"""
Thermal Receipt Printer CLI

Print markdown, text, and images to an Epson TM-T88V thermal printer.

ENVIRONMENT VARIABLES:
    THERMAL_PRINTER_CONNECTION  Printer connection: network or usb (default: network)
    THERMAL_PRINTER_IP    Printer IP address (default: 192.168.2.2)
    THERMAL_PRINTER_PORT  Printer port (default: 9100)
    THERMAL_PRINTER_USB_VENDOR_ID   USB vendor ID from lsusb
    THERMAL_PRINTER_USB_PRODUCT_ID  USB product ID from lsusb

EXAMPLES:
    # Print a markdown file
    receipt print markdown/input.md

    # Print markdown string (use quotes for special chars)
    receipt print "# Hello World\n\nThis is **bold** text."

    # Print with custom printer IP
    receipt print --ip 192.168.1.100 "# Receipt"

    # Print from stdin
    echo "# Hello" | receipt print -

    # Print an image
    receipt image photo.jpg

    # Print image from URL
    receipt image "https://example.com/logo.png"

    # Cut paper after printing
    receipt print --cut "# Thanks for visiting!"

    # Just cut paper
    receipt cut

LLM USAGE:
    When calling from an LLM, use these patterns:

    1. Simple text with markdown:
       receipt print "# Title\\n\\nBody text with **bold**."

    2. File path (absolute paths recommended):
       receipt print /path/to/document.md

    3. With images in markdown (absolute URLs or paths):
       receipt print "# Order\\n\\n![Logo](https://example.com/logo.png)\\n\\nThank you!"

    4. Escaping special characters:
       - Newlines: Use \\n
       - Quotes: Use \\" or single quotes around the string
       - Dollar signs: Use \\$ or single quotes

    5. Multi-line with heredoc (bash):
       receipt print <<'EOF'
       # Receipt

       Item 1: $10.00
       Item 2: $20.00

       **Total: $30.00**
       EOF
"""

import argparse
import os
import sys
from pathlib import Path


def get_printer_config(args):
    """Get printer IP and port from args or environment."""
    from printer_utils import DEFAULT_PRINTER_IP, DEFAULT_PRINTER_PORT

    connection = (args.connection or os.environ.get('THERMAL_PRINTER_CONNECTION', 'network')).lower()
    ip = args.ip or os.environ.get('THERMAL_PRINTER_IP', DEFAULT_PRINTER_IP)
    port = args.port or int(os.environ.get('THERMAL_PRINTER_PORT', str(DEFAULT_PRINTER_PORT)))
    return connection, ip, port


def describe_printer(args):
    """Return a human-readable printer target for status messages."""
    connection, ip, port = get_printer_config(args)
    if connection == 'usb':
        vendor_id = args.usb_vendor_id or os.environ.get('THERMAL_PRINTER_USB_VENDOR_ID', 'unknown')
        product_id = args.usb_product_id or os.environ.get('THERMAL_PRINTER_USB_PRODUCT_ID', 'unknown')
        return f'USB printer {vendor_id}:{product_id}'
    return f'{ip}:{port}'


def get_printer(args):
    """Initialize and return printer instance."""
    from printer_utils import ThermalPrinter
    return ThermalPrinter.from_env(
        connection=args.connection,
        ip_address=args.ip,
        port=args.port,
        usb_vendor_id=args.usb_vendor_id,
        usb_product_id=args.usb_product_id,
        usb_in_endpoint=args.usb_in_endpoint,
        usb_out_endpoint=args.usb_out_endpoint,
        usb_timeout=args.usb_timeout,
    )


def read_input(source):
    """Read content from file path, stdin, or treat as string."""
    # Read from stdin
    if source == '-':
        return sys.stdin.read()

    # Check if it's a file path
    path = Path(source)
    if path.exists() and path.is_file():
        return path.read_text()

    # Treat as literal string, process escape sequences
    return source.encode().decode('unicode_escape')


def cmd_print(args):
    """Print markdown content."""
    content = read_input(args.content)

    with get_printer(args) as printer:
        printer.print_markdown(content)
        if args.cut:
            printer.cut_paper()

    print(f"Printed to {describe_printer(args)}", file=sys.stderr)


def cmd_text(args):
    """Print plain text."""
    content = read_input(args.content)

    with get_printer(args) as printer:
        printer.print_text(content, bold=args.bold)
        if args.cut:
            printer.cut_paper()

    print(f"Printed to {describe_printer(args)}", file=sys.stderr)


def cmd_image(args):
    """Print an image."""
    with get_printer(args) as printer:
        printer.print_image(args.path)
        if args.cut:
            printer.cut_paper()

    print(f"Printed image to {describe_printer(args)}", file=sys.stderr)


def cmd_cut(args):
    """Cut the paper."""
    with get_printer(args) as printer:
        printer.cut_paper()
    print(f"Paper cut on {describe_printer(args)}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        prog='receipt',
        description='Print to Epson TM-T88V thermal receipt printer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Environment Variables:
  THERMAL_PRINTER_CONNECTION  Printer connection: network or usb (default: network)
  THERMAL_PRINTER_IP    Printer IP address (default: 192.168.2.2)
  THERMAL_PRINTER_PORT  Printer port (default: 9100)
  THERMAL_PRINTER_USB_VENDOR_ID   USB vendor ID from lsusb
  THERMAL_PRINTER_USB_PRODUCT_ID  USB product ID from lsusb

Examples:
  receipt print "# Hello World"
  receipt print /path/to/file.md
  receipt print --cut "# Receipt\\n\\nThank you!"
  receipt image logo.png
  receipt cut

  # Using environment variable
  THERMAL_PRINTER_IP=192.168.1.100 receipt print "# Test"
'''
    )

    # Global options
    parser.add_argument('--connection', choices=('network', 'usb'), help='Printer connection type (or set THERMAL_PRINTER_CONNECTION)')
    parser.add_argument('--ip', help='Network printer IP address (or set THERMAL_PRINTER_IP)')
    parser.add_argument('--port', type=int, help='Network printer port (or set THERMAL_PRINTER_PORT)')
    parser.add_argument('--usb-vendor-id', help='USB printer vendor ID, decimal or hex (or set THERMAL_PRINTER_USB_VENDOR_ID)')
    parser.add_argument('--usb-product-id', help='USB printer product ID, decimal or hex (or set THERMAL_PRINTER_USB_PRODUCT_ID)')
    parser.add_argument('--usb-in-endpoint', help='USB input endpoint, decimal or hex (default: 0x82)')
    parser.add_argument('--usb-out-endpoint', help='USB output endpoint, decimal or hex (default: 0x01)')
    parser.add_argument('--usb-timeout', help='USB timeout in milliseconds (default: 0)')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # print command (markdown)
    print_parser = subparsers.add_parser(
        'print',
        help='Print markdown content',
        description='''
Print markdown content to the thermal printer.

Supports:
  - Headers (# ## ###)
  - Bold text (**text** or __text__)
  - Lists (- item or 1. item)
  - Images (![alt](path_or_url))

Input can be:
  - A file path (prints file contents)
  - A markdown string (with \\n for newlines)
  - "-" to read from stdin
'''
    )
    print_parser.add_argument('content', help='Markdown string, file path, or "-" for stdin')
    print_parser.add_argument('--cut', '-c', action='store_true', help='Cut paper after printing')
    print_parser.set_defaults(func=cmd_print)

    # text command (plain text)
    text_parser = subparsers.add_parser(
        'text',
        help='Print plain text',
        description='Print plain text without markdown processing.'
    )
    text_parser.add_argument('content', help='Text string, file path, or "-" for stdin')
    text_parser.add_argument('--bold', '-b', action='store_true', help='Print in bold')
    text_parser.add_argument('--cut', '-c', action='store_true', help='Cut paper after printing')
    text_parser.set_defaults(func=cmd_text)

    # image command
    image_parser = subparsers.add_parser(
        'image',
        help='Print an image',
        description='Print an image with Bayer matrix dithering. Accepts local file paths or URLs.'
    )
    image_parser.add_argument('path', help='Image file path or URL')
    image_parser.add_argument('--cut', '-c', action='store_true', help='Cut paper after printing')
    image_parser.set_defaults(func=cmd_image)

    # cut command
    cut_parser = subparsers.add_parser('cut', help='Cut the paper')
    cut_parser.set_defaults(func=cmd_cut)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print('\nCancelled', file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
