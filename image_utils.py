from enum import Enum
from PIL import Image
import numpy as np
from typing import Union
import os

class DitherMethod(Enum):
    BAYER_32x32 = "bayer_32x32"
    CLUSTERED_DOT_6 = "clustered_dot_6"
    VARIABLE_2x2 = "variable_2x2"

class ImageDitherer:
    def __init__(self):
        # Initialize dither matrices
        self.bayer_32x32 = self._generate_bayer_matrix(32)
        self.clustered_dot_6 = np.array([
            [34, 29, 17, 21, 30, 35],
            [28, 14,  9, 16, 20, 31],
            [13,  8,  4,  5, 15, 19],
            [12,  3,  0,  1,  6, 18],
            [27,  7,  2, 10, 22, 33],
            [33, 26, 11, 24, 32, 36]
        ]) / 36.0
        
        self.variable_2x2 = np.array([
            [0, 2],
            [3, 1]
        ]) / 4.0

    def _generate_bayer_matrix(self, n: int) -> np.ndarray:
        """Generate an n×n Bayer matrix"""
        if n & (n - 1) != 0:
            raise ValueError("n must be a power of 2")
            
        # Initialize 2×2 Bayer matrix
        matrix = np.array([[0, 2],
                          [3, 1]], dtype=np.float32)
        
        size = 2
        while size < n:
            matrix = np.block([[4*matrix,     4*matrix + 2],
                             [4*matrix + 3,   4*matrix + 1]])
            size *= 2
            
        return matrix / (n * n)

    def _apply_dither_matrix(self, image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """Apply dither matrix to image"""
        # Ensure image is normalized to [0, 1]
        if image.max() > 1:
            image = image / 255.0
            
        # Tile the dither matrix to match image size
        h, w = image.shape
        mh, mw = matrix.shape
        dither_tiled = np.tile(matrix, (((h + mh - 1) // mh), ((w + mw - 1) // mw)))[:h, :w]
        
        # Apply threshold - changed from <= to > to fix inversion
        return (image > dither_tiled).astype(np.uint8) * 255

    def dither_image(self, image_path: Union[str, Image.Image], method: DitherMethod) -> Image.Image:
        """Dither an image using specified method"""
        # Load image if path provided
        if isinstance(image_path, str):
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image = Image.open(image_path)
        else:
            image = image_path

        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
            
        # Convert to numpy array
        img_array = np.array(image)
        
        # Apply appropriate dither matrix
        if method == DitherMethod.BAYER_32x32:
            dithered = self._apply_dither_matrix(img_array, self.bayer_32x32)
        elif method == DitherMethod.CLUSTERED_DOT_6:
            dithered = self._apply_dither_matrix(img_array, self.clustered_dot_6)
        elif method == DitherMethod.VARIABLE_2x2:
            dithered = self._apply_dither_matrix(img_array, self.variable_2x2)
        else:
            raise ValueError(f"Unknown dither method: {method}")
            
        # Convert back to PIL Image
        return Image.fromarray(dithered, mode='L') 