import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .url_filter import is_valid_url

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def crawl_urls(max_pages=1000):

    visited = set()

    seed_urls = [

        "https://www.srmist.edu.in/",
        "https://www.srmist.edu.in/admissions/",
        "https://www.srmist.edu.in/academics/",
        "https://www.srmist.edu.in/research/",
        "https://www.srmist.edu.in/campus-life/",
        "https://www.srmist.edu.in/career-centre/",
        "https://www.srmist.edu.in/faculty-of-engineering-and-technology/",
        "https://www.srmist.edu.in/college/college-of-engineering-technology/"

    ]

    queue = seed_urls.copy()

    collected_urls = []

    while queue and len(collected_urls) < max_pages:

        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(
                response.text,
                "lxml"
            )

            if is_valid_url(url):

                collected_urls.append(url)

            for tag in soup.find_all(
                "a",
                href=True
            ):

                link = urljoin(
                    url,
                    tag["href"]
                )

                if (
                    link not in visited
                    and
                    is_valid_url(link)
                ):

                    queue.append(link)

        except Exception as e:

            print(
                "Crawl Error:",
                e
            )

    print(
        f"Crawler discovered {len(collected_urls)} URLs"
    )

    return collected_urls