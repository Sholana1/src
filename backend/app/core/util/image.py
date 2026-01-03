from PIL import Image, UnidentifiedImageError
import io
from typing import Tuple
from backend.app.core.logging import get_logger
from backend.app.core.config import settings

logger = get_logger()

def validate_image(file_data:bytes) -> Tuple[bool, str]:
    try:
        file_size_mb = len(file_data) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            return(
                False,
                f"file size exceeds {settings.MAX_FILE_SIZE_MB/1024*1024}MB"
            )
        image_buffer = io.BytesIO(file_data)
        
        with Image.open(image_buffer) as img:
            if img.format is None or img.format.lower() not in ["jpeg", "png", "jpg"]:
                return False, "Invalid image format. Only JPEG and PNG are allowed."
            
            width, height = img.size
            if width > settings.MAX_DIMENSION or height > settings.MAX_DIMENSION:
                return (
                    False,
                    f"Image dimensions exceed the maximum allowed size of {settings.MAX_DIMENSION}px."
                )
            try:
                img.load()
            except Exception as e:
                logger.error(f"Image data is corrupted: {e}")
                return False, "Image data is corrupted."
            
        return True, "Image is valid."
    except UnidentifiedImageError:
        return False, "File is not a valid image."
    except Exception as e:
        logger.error(f"Unexpected error during image validation: {e}")
        return False, "An unexpected error occurred during image validation."