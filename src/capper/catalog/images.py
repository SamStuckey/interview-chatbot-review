"""Product images: SVG assets shipped in the package and image, served by the app.

The supplied catalog has no images, so each product has an illustrative SVG
named after it. A product's `image_url` is the path the app serves it at.
"""

import re
from pathlib import Path

PRODUCT_IMAGES = Path(__file__).parent / "product_images"
URL_PREFIX = "/images/products"


def image_slug(name: str) -> str:
    """`Macaroni & Cheese Box` → `macaroni-cheese-box`."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def product_image_url(name: str) -> str:
    return f"{URL_PREFIX}/{image_slug(name)}.svg"
