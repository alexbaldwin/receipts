from enum import Enum
from PIL import Image
import numpy as np

class DitherMethod(Enum):
    BAYER_32x32 = "bayer_32x32"
    CLUSTERED_DOT_6 = "clustered_dot_6"
    VARIABLE_2x2 = "variable_2x2"

class ImageDitherer:
    def __init__(self):
        # Initialize dither matrices
        self.bayer_32x32 = self._create_bayer_matrix(32)
        self.clustered_dot_6 = self._create_clustered_dot_matrix()
        self.variable_2x2 = np.array([[0, 2], [3, 1]]) / 4.0

    def dither_image(self, image_path, method):
        # Load and convert image to grayscale
        img = Image.open(image_path).convert('L')
        img_array = np.array(img)
        
        if method == DitherMethod.BAYER_32x32:
            return self._apply_dither(img_array, self.bayer_32x32)
        elif method == DitherMethod.CLUSTERED_DOT_6:
            return self._apply_dither(img_array, self.clustered_dot_6)
        elif method == DitherMethod.VARIABLE_2x2:
            return self._apply_dither(img_array, self.variable_2x2)
        else:
            raise ValueError(f"Unknown dither method: {method}")

    def _apply_dither(self, img_array, matrix):
        h, w = img_array.shape
        m_h, m_w = matrix.shape
        
        # Normalize image to 0-1
        img_normalized = img_array / 255.0
        
        # Tile the dither matrix to match image size
        matrix_tiled = np.tile(matrix, (h // m_h + 1, w // m_w + 1))
        matrix_tiled = matrix_tiled[:h, :w]
        
        # Apply dithering
        dithered = img_normalized > matrix_tiled
        
        # Convert back to PIL Image
        return Image.fromarray(dithered.astype(np.uint8) * 255)

    def _create_bayer_matrix(self, n):
        if n == 1:
            return np.array([[0]])
        
        smaller = self._create_bayer_matrix(n // 2)
        return np.block([[4 * smaller, 4 * smaller + 2],
                        [4 * smaller + 3, 4 * smaller + 1]]) / (n * n)

    def _create_clustered_dot_matrix(self):
        return np.array([
            [13, 11, 12, 15, 16, 14],
            [7,  4,  5,  8,  9,  6],
            [10, 1,  2,  3,  17, 18],
            [19, 22, 21, 20, 23, 24],
            [25, 28, 29, 26, 32, 30],
            [31, 34, 35, 33, 36, 27]
        ]) / 36.0 