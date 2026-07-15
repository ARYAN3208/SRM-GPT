import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ]
)

adapter = HTTPAdapter(
    max_retries=retry
)

session.mount(
    "https://",
    adapter
)

session.mount(
    "http://",
    adapter
)

HEADERS = {

    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0 Safari/537.36",

    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",

    "Accept-Language":
    "en-US,en;q=0.5",

    "Referer":
    "https://www.google.com/",

    "Connection":
    "keep-alive"
}

def parse_page(url):

    try:

        response = session.get(
            url,
            headers=HEADERS,
            timeout=40
        )

        print(
            f"{response.status_code} -> {url}"
        )

        if response.status_code != 200:

            print(
                f"Skipped {response.status_code}: {url}"
            )

            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "iframe",
            "noscript"
        ]):
            tag.decompose()

        main_content = soup.find("main")

        if main_content:

            text = main_content.get_text(
                separator=" ",
                strip=True
            )

        else:

            text = soup.get_text(
                separator=" ",
                strip=True
            )

        text = " ".join(
            text.split()
        )

        if not text.strip():
            return None

        title = ""

        if soup.title:

            title = soup.title.get_text(
                strip=True
            )

        return {

            "source":
            "website",

            "url":
            url,

            "title":
            title,

            "text":
            text

        }

    except Exception as e:

        print(
            f"Error {url}: {e}"
        )

        return None