import requests
from bs4 import BeautifulSoup

HEADERS = {

    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",

    "Accept-Language":
    "en-US,en;q=0.9"

}

def scrape_page(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:

            print(
                response.status_code,
                "Forbidden",
                url
            )

            return None

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )

        return soup

    except Exception as e:

        print(
            "Scrape Error:",
            e
        )

        return None