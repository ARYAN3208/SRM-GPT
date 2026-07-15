import requests
from bs4 import BeautifulSoup

session = requests.Session()

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

def get_pdf_links(url):

    pdf_links = []

    try:

        print(
            f"Checking: {url}"
        )

        response = session.get(

            url,
            headers=HEADERS,
            timeout=20

        )

        print(
            "Status:",
            response.status_code
        )

        if response.status_code != 200:

            return []

        soup = BeautifulSoup(

            response.text,
            "html.parser"

        )

        links = soup.find_all(

            "a",
            href=True

        )

        print(
            "Total links:",
            len(links)
        )

        for link in links:

            href = link["href"]

            if ".pdf" in href.lower():

                if href.startswith("/"):

                    href = (
                        "https://www.srmist.edu.in"
                        + href
                    )

                print(
                    "PDF FOUND:",
                    href
                )

                pdf_links.append(
                    href
                )

    except Exception as e:

        print(
            "PDF Link Error:",
            e
        )

    return list(
        set(pdf_links)
    )