import requests
from bs4 import BeautifulSoup

from .url_filter import is_valid_url

SITEMAP_URL = (
    "https://www.srmist.edu.in/sitemap.xml"
)

TARGET_SITEMAPS = [

    "faculties-sitemap",
    "events-sitemap",
    "post-archive-sitemap"

]

def load_sitemap():

    headers = {

        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",

        "Accept":
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",

        "Accept-Language":
        "en-US,en;q=0.9",

        "Referer":
        "https://www.google.com/"

    }

    try:

        response = requests.get(
            SITEMAP_URL,
            headers=headers,
            timeout=30
        )

        print(
            "URL:",
            response.url
        )

        print(
            "Sitemap Status:",
            response.status_code
        )

        if response.status_code != 200:
            return []

        sitemap_index = BeautifulSoup(
            response.text,
            "xml"
        )

        sitemap_urls = []

        for loc in sitemap_index.find_all(
            "loc"
        ):

            sitemap_urls.append(
                loc.text.strip()
            )

        print(
            f"Sitemaps Found: {len(sitemap_urls)}"
        )

        all_urls = []

        for sitemap_url in sitemap_urls:

            if not any(
                target in sitemap_url.lower()
                for target in TARGET_SITEMAPS
            ):
                continue

            print(
                f"\nProcessing: {sitemap_url}"
            )

            try:

                child_response = requests.get(
                    sitemap_url,
                    headers=headers,
                    timeout=30
                )

                if child_response.status_code != 200:
                    continue

                child_soup = BeautifulSoup(
                    child_response.text,
                    "xml"
                )

                count = 0

                for loc in child_soup.find_all(
                    "loc"
                ):

                    url = loc.text.strip()

                    if is_valid_url(url):

                        all_urls.append(
                            url
                        )

                        count += 1

                print(
                    f"{sitemap_url} -> {count} URLs"
                )

            except Exception as e:

                print(
                    "Child Sitemap Error:",
                    e
                )

        all_urls = list(
            set(all_urls)
        )

        print(
            f"\nTotal New URLs Loaded: {len(all_urls)}"
        )

        return all_urls

    except Exception as e:

        print(
            "Sitemap Error:",
            e
        )

        return []