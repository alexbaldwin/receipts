from escpos.printer import Network, Usb
from PIL import Image
import os
import re
import PIL.ImageOps
import PIL.ImageEnhance
import numpy
import requests
from urllib.parse import urlparse
from io import BytesIO
import textwrap


DEFAULT_PRINTER_IP = "192.168.2.2"
DEFAULT_PRINTER_PORT = 9100


def _parse_int(value, name):
    """Parse decimal or 0x-prefixed integer config values."""
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value), 0)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer or hex value, got {value!r}") from exc


class ThermalPrinter:
    def __init__(
        self,
        ip_address=None,
        port=None,
        connection=None,
        usb_vendor_id=None,
        usb_product_id=None,
        usb_in_endpoint=None,
        usb_out_endpoint=None,
        usb_timeout=None,
        printer_backend=None,
        initialize=True,
    ):
        """Initialize a network or USB printer connection."""
        # TM-T88V specific settings
        self.MAX_WIDTH = 512  # Standard width for TM-T88V
        self.DPI = 180       # Standard DPI
        self.CHARS_PER_LINE = 42  # Approximate characters that fit on one line

        self.connection = (connection or os.environ.get("THERMAL_PRINTER_CONNECTION") or "network").lower()
        self.printer = printer_backend or self._build_backend(
            ip_address=ip_address,
            port=port,
            usb_vendor_id=usb_vendor_id,
            usb_product_id=usb_product_id,
            usb_in_endpoint=usb_in_endpoint,
            usb_out_endpoint=usb_out_endpoint,
            usb_timeout=usb_timeout,
        )

        if initialize:
            self._raw(b'\x1b\x40')  # ESC @ - Initialize printer

    @classmethod
    def from_env(cls, **overrides):
        """Create a printer using THERMAL_PRINTER_* environment variables."""
        return cls(**overrides)

    def _build_backend(
        self,
        ip_address=None,
        port=None,
        usb_vendor_id=None,
        usb_product_id=None,
        usb_in_endpoint=None,
        usb_out_endpoint=None,
        usb_timeout=None,
    ):
        if self.connection == "network":
            host = ip_address or os.environ.get("THERMAL_PRINTER_IP", DEFAULT_PRINTER_IP)
            printer_port = _parse_int(port or os.environ.get("THERMAL_PRINTER_PORT", DEFAULT_PRINTER_PORT), "THERMAL_PRINTER_PORT")
            return Network(host, printer_port)

        if self.connection == "usb":
            vendor_id = _parse_int(
                usb_vendor_id or os.environ.get("THERMAL_PRINTER_USB_VENDOR_ID"),
                "THERMAL_PRINTER_USB_VENDOR_ID",
            )
            product_id = _parse_int(
                usb_product_id or os.environ.get("THERMAL_PRINTER_USB_PRODUCT_ID"),
                "THERMAL_PRINTER_USB_PRODUCT_ID",
            )
            if vendor_id is None or product_id is None:
                raise ValueError(
                    "USB printing requires THERMAL_PRINTER_USB_VENDOR_ID and "
                    "THERMAL_PRINTER_USB_PRODUCT_ID"
                )

            in_endpoint = _parse_int(
                usb_in_endpoint or os.environ.get("THERMAL_PRINTER_USB_IN_ENDPOINT", "0x82"),
                "THERMAL_PRINTER_USB_IN_ENDPOINT",
            )
            out_endpoint = _parse_int(
                usb_out_endpoint or os.environ.get("THERMAL_PRINTER_USB_OUT_ENDPOINT", "0x01"),
                "THERMAL_PRINTER_USB_OUT_ENDPOINT",
            )
            timeout = _parse_int(
                usb_timeout or os.environ.get("THERMAL_PRINTER_USB_TIMEOUT", "0"),
                "THERMAL_PRINTER_USB_TIMEOUT",
            )
            return Usb(vendor_id, product_id, timeout=timeout, in_ep=in_endpoint, out_ep=out_endpoint)

        raise ValueError("THERMAL_PRINTER_CONNECTION must be 'network' or 'usb'")
        
    def _raw(self, data):
        """Send raw bytes to printer"""
        self.printer._raw(data)

    def close(self):
        """Release the printer connection so the next job can open it."""
        backend = getattr(self, "printer", None)
        if backend is None:
            return
        close = getattr(backend, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass
        self.printer = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
        
    def print_text(self, text, bold=False):
        """Print text with basic formatting"""
        try:
            if bold:
                self._raw(b'\x1b\x45\x01')  # Bold ON
            
            # Convert text to bytes and print
            self._raw(text.encode('ascii', 'replace'))
            self._raw(b'\n')
            
            if bold:
                self._raw(b'\x1b\x45\x00')  # Bold OFF
                
        except Exception as e:
            print(f"Error printing text: {str(e)}")
            raise
    
    def _get_bayer_matrix(self, n=8):
        """Generate an n×n Bayer matrix for ordered dithering"""
        # Initialize 2×2 Bayer matrix
        matrix = numpy.array([[0, 2],
                             [3, 1]], dtype=numpy.float32)
        
        # Scale up matrix to desired size using recursive doubling
        size = 2
        while size < n:
            matrix = numpy.bmat([[4*matrix, 4*matrix+2],
                               [4*matrix+3, 4*matrix+1]])
            size *= 2
        
        # Normalize matrix values to [0, 1]
        return matrix / (n * n)
    
    def print_image(self, image_path):
        """Print image using ordered dithering (Bayer matrix) with correct black/white mapping"""
        try:
            # Check if image_path is a URL
            parsed = urlparse(image_path)
            if parsed.scheme in ('http', 'https'):
                # Download image from URL
                response = requests.get(image_path, timeout=30)
                response.raise_for_status()  # Raise exception for bad status codes
                image = Image.open(BytesIO(response.content))
            else:
                # Open local file
                image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            ratio = self.MAX_WIDTH / image.width
            new_height = int(image.height * ratio)
            
            # Resize image to printer width
            image = image.resize((self.MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Convert image to numpy array and normalize to [0, 1]
            img_array = numpy.array(image) / 255.0
            
            # Get 8×8 Bayer matrix
            bayer = self._get_bayer_matrix(8)
            
            # Tile Bayer matrix across the image
            h, w = img_array.shape
            bayer_tiled = numpy.tile(bayer, (((h + 7) // 8), ((w + 7) // 8)))[:h, :w]
            
            # Apply ordered dithering with inverted comparison for correct black/white mapping
            dithered = (img_array <= bayer_tiled).astype(numpy.uint8) * 255
            
            # Convert back to PIL Image
            dithered_image = Image.fromarray(dithered.astype(numpy.uint8), mode='L')
            dithered_image = dithered_image.convert('1')
            
            # Ensure width is multiple of 8 (required by printer)
            width_bytes = (self.MAX_WIDTH + 7) // 8
            
            # Send image using raster bit image command
            self._raw(b'\x1d\x76\x30\x00')  # GS v 0 \0
            self._raw(bytes([width_bytes & 0xff, width_bytes >> 8]))  # width
            self._raw(bytes([new_height & 0xff, new_height >> 8]))   # height
            
            # Send the image data
            self._raw(dithered_image.tobytes())
            
            
        except Exception as e:
            print(f"Error printing image: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def cut_paper(self):
        """Perform a full cut with padding"""
        # Add some padding before cutting (2 more line feeds)
        self._raw(b'\x1b\x64\x02')  # ESC d n - Feed n lines
        # Perform the cut
        self._raw(b'\x1d\x56\x00')  # GS V \0
    
    def _wrap_text(self, text, width=None):
        """Wrap text to fit printer width"""
        if width is None:
            width = self.CHARS_PER_LINE
        return textwrap.fill(text, width=width, break_long_words=True, break_on_hyphens=True)
    
    def print_markdown(self, markdown_text):
        """Print text with markdown formatting"""
        try:
            # Split into lines for processing
            lines = markdown_text.split('\n')
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    self._raw(b'\n')
                    continue
                
                # Check for images first - ![alt text](image.jpg)
                image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line.strip())
                if image_match:
                    # Extract alt text and image path
                    alt_text = image_match.group(1)
                    image_path = image_match.group(2)
                    
                    # Add spacing before image
                    self._raw(b'\n')
                    
                    # Print the image using our dithering method
                    self.print_image(image_path)
                    
                    # Print alt text if it exists
                    if alt_text:
                        # Add TWO newlines before alt text for better spacing
                        self._raw(b'\n')
                        
                        self._raw(b'\x1b\x45\x01')  # Bold ON
                        wrapped_text = self._wrap_text(alt_text)
                        for wrapped_line in wrapped_text.splitlines():
                            self._raw(wrapped_line.encode('ascii', 'replace'))
                            self._raw(b'\n')
                        self._raw(b'\x1b\x45\x00')  # Bold OFF
                    
                    continue
                
                # Headers
                if line.startswith('#'):
                    level = len(re.match(r'^#+', line).group())
                    text = line[level:].strip()
                    
                    # Make headers bold
                    self._raw(b'\x1b\x45\x01')  # Bold ON
                    
                    # Different sizes for different header levels
                    if level == 1:
                        self._raw(b'\x1b\x21\x30')  # Double width/height
                        wrapped_text = self._wrap_text(text, width=self.CHARS_PER_LINE // 2)
                    elif level == 2:
                        # Add consistent padding before h2
                        self._raw(b'\n')
                        
                        self._raw(b'\x1b\x21\x20')  # Double width
                        wrapped_text = self._wrap_text(text, width=self.CHARS_PER_LINE // 2)
                    else:
                        wrapped_text = self._wrap_text(text)
                    
                    for wrapped_line in wrapped_text.splitlines():
                        self._raw(wrapped_line.encode('ascii', 'replace'))
                        self._raw(b'\n')
                    
                    # Reset formatting
                    self._raw(b'\x1b\x21\x00')  # Normal size
                    self._raw(b'\x1b\x45\x00')  # Bold OFF
                    
                    # Add consistent padding after headers
                    # Extra padding for h2
                    self._raw(b'\n')
                    
                # Lists
                elif line.strip().startswith(('- ', '* ', '+ ')):
                    text = line.strip()[2:]  # Remove list marker
                    wrapped_text = self._wrap_text(text, width=self.CHARS_PER_LINE - 4)  # Account for indent
                    first_line = True
                    for wrapped_line in wrapped_text.splitlines():
                        if first_line:
                            self._raw(b'  \x2A ')  # Using '*' as bullet point
                            first_line = False
                        else:
                            self._raw(b'    ')  # Indent continuation lines
                        self._raw(wrapped_line.encode('ascii', 'replace'))
                        self._raw(b'\n')
                
                # Numbered lists
                elif re.match(r'^\d+\.', line.strip()):
                    number = re.match(r'^\d+', line.strip()).group()
                    text = re.sub(r'^\d+\.\s*', '', line.strip())
                    indent = len(number) + 2  # number + dot + space
                    wrapped_text = self._wrap_text(text, width=self.CHARS_PER_LINE - indent - 2)
                    first_line = True
                    for wrapped_line in wrapped_text.splitlines():
                        if first_line:
                            self._raw(f"  {number}. ".encode('ascii', 'replace'))
                            first_line = False
                        else:
                            self._raw(b' ' * (indent + 2))  # Indent continuation lines
                        self._raw(wrapped_line.encode('ascii', 'replace'))
                        self._raw(b'\n')
                
                # Bold text
                elif '**' in line or '__' in line:
                    parts = re.split(r'(\*\*.*?\*\*|__.*?__)', line)
                    wrapped_text = ''
                    for part in parts:
                        if part.startswith(('**', '__')) and part.endswith(('**', '__')):
                            wrapped_text += f"\x1b\x45\x01{part[2:-2]}\x1b\x45\x00"
                        else:
                            wrapped_text += part
                    
                    for wrapped_line in self._wrap_text(wrapped_text).splitlines():
                        self._raw(wrapped_line.encode('ascii', 'replace'))
                        self._raw(b'\n')
                
                # Regular text
                else:
                    wrapped_text = self._wrap_text(line)
                    for wrapped_line in wrapped_text.splitlines():
                        self._raw(wrapped_line.encode('ascii', 'replace'))
                        self._raw(b'\n')
            
            # Add two newlines at the end of all markdown content
            self._raw(b'\n\n')
            
        except Exception as e:
            print(f"Error printing markdown: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def print_ascii_art(self, image_path, width=512, chars=" .:-=+#@"):
        """Convert image to ASCII art and print it"""
        try:
            # Open and process image
            image = Image.open(image_path)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Calculate new dimensions
            aspect_ratio = image.height / image.width
            new_width = width
            new_height = int(aspect_ratio * width * 0.5)  # * 0.5 to account for character aspect ratio
            
            # Resize image maintaining aspect ratio
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Enhance contrast before conversion
            image = PIL.ImageEnhance.Contrast(image).enhance(1.5)
            image = PIL.ImageEnhance.Brightness(image).enhance(1.2)
            
            # Convert to 1-bit black and white
            image = PIL.ImageOps.invert(image)
            image = image.convert('1')
            
            # Make sure width is multiple of 8
            if new_width % 8:
                padded_width = new_width + (8 - new_width % 8)
                padded_image = Image.new('1', (padded_width, new_height), 'white')
                padded_image.paste(image, (0, 0))
                image = padded_image
            
            # Print using ESC/POS raster format
            width_bytes = int(image.width / 8)
            
            # GS v 0 \0 command for full-width printing
            self._raw(b'\x1d\x76\x30\x00')
            # Width bytes (low, high)
            self._raw(bytes([width_bytes & 0xff, width_bytes >> 8]))
            # Height bytes (low, high)
            self._raw(bytes([image.height & 0xff, image.height >> 8]))
            # Image data
            self._raw(image.tobytes())
            
            # Add padding
            self._raw(b'\x1b\x64\x04')  # Feed 4 lines
            
        except Exception as e:
            print(f"Error creating ASCII art: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
