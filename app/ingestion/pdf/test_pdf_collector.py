import json
import os

from .pdf_link_scraper import get_pdf_links
from .pdf_downloader import download_pdf

WEBSITE_DATA = (
    "app/data/raw/ktr_website_data.json"
)

with open(
    WEBSITE_DATA,
    "r",
    encoding="utf-8"
) as f:

    website_pages = json.load(f)

all_links = []

for index, item in enumerate(
    website_pages,
    start=1
):

    url = item.get("url")

    if url:

        links = get_pdf_links(url)

        all_links.extend(links)

    if index % 100 == 0:

        os.makedirs(
            "app/data/raw",
            exist_ok=True
        )

        with open(
            "app/data/raw/pdf_links_checkpoint.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                list(set(all_links)),
                f,
                indent=4
            )

        print(
            f"Checkpoint saved at {index}"
        )

all_links = list(
    set(all_links)
)

with open(
    "app/data/raw/pdf_links.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_links,
        f,
        indent=4
    )

print(
    f"PDF links found: {len(all_links)}"
)

for index, link in enumerate(
    all_links,
    start=1
):

    download_pdf(
        link,
        "app/data/uploads"
    )

    if index % 100 == 0:

        print(
            f"Downloaded {index}/{len(all_links)} PDFs"
        )