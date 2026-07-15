import json
import os

from .image_scraper import (
    download_images_from_page
)

WEBSITE_DATA = (
    "app/data/raw/ktr_website_data.json"
)

with open(
    WEBSITE_DATA,
    "r",
    encoding="utf-8"
) as f:

    website_pages = json.load(f)

SAVE_FOLDER = (
    "app/data/uploads/site_images"
)

for index, item in enumerate(
    website_pages,
    start=1
):

    url = item.get(
        "url"
    )

    if not url:
        continue

    print(
        f"[{index}/{len(website_pages)}] {url}"
    )

    download_images_from_page(
        url,
        SAVE_FOLDER
    )

print(
    "Image scraping completed."
)