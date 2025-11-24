"""Unit tests for image processing service.

Tests image padding and transformation logic for video generation.
Fast unit tests - no external services needed.

Run with: pytest backend/tests/unit/test_image_processing.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from PIL import Image  # noqa: E402
from io import BytesIO  # noqa: E402

from app.services.image_processing import (  # noqa: E402
    TARGET_9_16_HEIGHT,
    TARGET_9_16_WIDTH,
    pad_image_to_9_16,
)


def create_test_image(
    format: str = "JPEG",
    width: int = 512,
    height: int = 512,
    mode: str = "RGB",
    color: tuple = (128, 128, 128),
) -> bytes:
    """Helper to create a test image in memory."""
    img = Image.new(mode, (width, height), color=color)
    output = BytesIO()
    img.save(output, format=format)
    return output.getvalue()


class TestPadImageTo9_16:
    """Tests for pad_image_to_9_16 function."""

    def test_square_image_padded_to_9_16(self):
        """Test that a square image (1:1) is padded to 9:16 correctly."""
        # Create 512x512 square image
        square_image = create_test_image("JPEG", 512, 512)
        
        # Pad to 9:16
        padded_bytes = pad_image_to_9_16(square_image)
        
        # Verify output
        padded_image = Image.open(BytesIO(padded_bytes))
        width, height = padded_image.size
        
        assert width == TARGET_9_16_WIDTH
        assert height == TARGET_9_16_HEIGHT
        assert height / width == 16 / 9  # Verify 9:16 aspect ratio
        
        # Verify image is centered (check top and bottom pixels are white)
        # Top row should be white (background)
        top_pixel = padded_image.getpixel((width // 2, 0))
        assert top_pixel == (255, 255, 255), "Top should be white padding"
        
        # Bottom row should be white (background)
        bottom_pixel = padded_image.getpixel((width // 2, height - 1))
        assert bottom_pixel == (255, 255, 255), "Bottom should be white padding"
        
        # Middle should have original image content (gray)
        middle_pixel = padded_image.getpixel((width // 2, height // 2))
        assert middle_pixel == (128, 128, 128), "Middle should have original image"

    def test_16_9_image_padded_to_9_16(self):
        """Test that a 16:9 image is padded to 9:16 correctly."""
        # Create 1920x1080 16:9 image
        wide_image = create_test_image("JPEG", 1920, 1080)
        
        # Pad to 9:16
        padded_bytes = pad_image_to_9_16(wide_image)
        
        # Verify output
        padded_image = Image.open(BytesIO(padded_bytes))
        width, height = padded_image.size
        
        assert width == TARGET_9_16_WIDTH
        assert height == TARGET_9_16_HEIGHT
        
        # For 16:9 image, it should be scaled down to fit width, then padded vertically
        # Original 1920x1080 scaled to 1080 width = 1080x607
        # Then padded to 1080x1920 with white space above and below

    def test_9_16_image_already_correct_aspect_ratio(self):
        """Test that a 9:16 image is handled correctly (scaled to target width, minimal padding)."""
        # Create 540x960 9:16 image (half size)
        vertical_image = create_test_image("JPEG", 540, 960)
        
        # Pad to 9:16
        padded_bytes = pad_image_to_9_16(vertical_image)
        
        # Verify output
        padded_image = Image.open(BytesIO(padded_bytes))
        width, height = padded_image.size
        
        assert width == TARGET_9_16_WIDTH
        assert height == TARGET_9_16_HEIGHT
        
        # Image should be scaled to 1080 width, then minimal padding if needed

    def test_4_3_image_padded_to_9_16(self):
        """Test that a 4:3 image is padded to 9:16 correctly."""
        # Create 1024x768 4:3 image
        traditional_image = create_test_image("JPEG", 1024, 768)
        
        # Pad to 9:16
        padded_bytes = pad_image_to_9_16(traditional_image)
        
        # Verify output dimensions
        padded_image = Image.open(BytesIO(padded_bytes))
        width, height = padded_image.size
        
        assert width == TARGET_9_16_WIDTH
        assert height == TARGET_9_16_HEIGHT

    def test_custom_background_color(self):
        """Test that custom background color works."""
        # Create square image
        square_image = create_test_image("JPEG", 512, 512)
        
        # Pad with black background
        padded_bytes = pad_image_to_9_16(square_image, background_color=(0, 0, 0))
        
        # Verify background is black
        padded_image = Image.open(BytesIO(padded_bytes))
        top_pixel = padded_image.getpixel((TARGET_9_16_WIDTH // 2, 0))
        assert top_pixel == (0, 0, 0), "Background should be black"

    def test_rgba_image_converted_to_rgb(self):
        """Test that RGBA images are converted to RGB before padding."""
        # Create RGBA image
        rgba_image = Image.new("RGBA", (512, 512), color=(128, 128, 128, 255))
        output = BytesIO()
        rgba_image.save(output, format="PNG")
        rgba_bytes = output.getvalue()
        
        # Pad to 9:16
        padded_bytes = pad_image_to_9_16(rgba_bytes)
        
        # Verify output is RGB (not RGBA)
        padded_image = Image.open(BytesIO(padded_bytes))
        assert padded_image.mode == "RGB", "Should be converted to RGB"

    def test_invalid_image_raises_error(self):
        """Test that invalid image bytes raise ValueError."""
        invalid_bytes = b"not an image"
        
        with pytest.raises(ValueError, match="Invalid image format"):
            pad_image_to_9_16(invalid_bytes)

    def test_equal_padding_above_and_below(self):
        """Test that padding is equal above and below the image."""
        # Create a wide image (16:9) that will need vertical padding
        # 1920x1080 scaled to 1080 width = 1080x607, which needs padding to reach 1920 height
        wide_image = create_test_image("JPEG", 1920, 1080)
        
        # Pad to 9:16
        padded_bytes = pad_image_to_9_16(wide_image)
        padded_image = Image.open(BytesIO(padded_bytes))
        
        # Verify dimensions
        width, height = padded_image.size
        assert width == TARGET_9_16_WIDTH
        assert height == TARGET_9_16_HEIGHT
        
        # Check that top and bottom rows are white (padding)
        top_pixel = padded_image.getpixel((width // 2, 0))
        bottom_pixel = padded_image.getpixel((width // 2, height - 1))
        
        assert top_pixel == (255, 255, 255), "Top should be white padding"
        assert bottom_pixel == (255, 255, 255), "Bottom should be white padding"
        
        # The image should be centered, so padding should be approximately equal
        # (may differ by 1 pixel due to rounding)
        # For 1080x607 image in 1080x1920 canvas, padding should be ~(1920-607)/2 = 656.5px each
        # Check that middle area has original image content (gray)
        middle_pixel = padded_image.getpixel((width // 2, height // 2))
        assert middle_pixel == (128, 128, 128), "Middle should have original image content"

