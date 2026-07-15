import json
import os

from .sitemap_loader import load_sitemap
from .parser import parse_page

print(
    "Loading sitemap..."
)

urls = load_sitemap()

print(
    f"Total URLs Found: {len(urls)}"
)

os.makedirs(
    "app/data/raw",
    exist_ok=True
)

output_path = (
    "app/data/raw/ktr_website_data.json"
)

parsed_data = []

for index, url in enumerate(
    urls,
    start=1
):

    print(
        f"[{index}/{len(urls)}] {url}"
    )

    data = parse_page(
        url
    )

    if data:

        parsed_data.append(
            data
        )

    if index % 100 == 0:

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                parsed_data,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"Checkpoint saved at {index}"
        )

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        parsed_data,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    f"Pages Parsed: {len(parsed_data)}"
)

print(
    f"Saved to {output_path}"
)