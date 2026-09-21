"""Modular receipt OCR. Providers can be swapped without changing views."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.conf import settings


@dataclass
class OCRResult:
    merchant: str | None = None
    date: str | None = None
    total: str | None = None
    line_items: list[dict] = field(default_factory=list)
    raw_text: str = ""
    provider: str = "none"
    available: bool = False
    message: str = ""


class BaseOCRProvider:
    name = "none"

    def extract(self, image_file) -> OCRResult:
        return OCRResult(
            provider=self.name,
            available=False,
            message="Receipt OCR is not configured. Review the photo and enter details yourself.",
        )


class TesseractOCRProvider(BaseOCRProvider):
    name = "tesseract"

    def extract(self, image_file) -> OCRResult:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return OCRResult(
                provider=self.name,
                available=False,
                message="Tesseract is not installed. Enter the receipt details manually.",
            )
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        return OCRResult(
            raw_text=text,
            provider=self.name,
            available=True,
            message="Review extracted information before saving.",
        )


def get_ocr_provider() -> BaseOCRProvider:
    name = getattr(settings, "OCR_PROVIDER", "none").lower()
    if name == "tesseract":
        return TesseractOCRProvider()
    return BaseOCRProvider()
