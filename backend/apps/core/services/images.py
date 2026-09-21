from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def compress_image(uploaded, max_size=1600, quality=82) -> ContentFile:
    image = Image.open(uploaded)
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    else:
        image = image.convert("RGB")
    image.thumbnail((max_size, max_size))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    name = getattr(uploaded, "name", "receipt.jpg")
    stem = name.rsplit(".", 1)[0]
    return ContentFile(buffer.getvalue(), name=f"{stem}.jpg")


def make_thumbnail(uploaded, size=320) -> ContentFile:
    image = Image.open(uploaded)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((size, size))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=70, optimize=True)
    return ContentFile(buffer.getvalue(), name="thumb.jpg")
