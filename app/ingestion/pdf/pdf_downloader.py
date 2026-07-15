import os
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def download_pdf(url, save_folder):

    try:

        os.makedirs(
            save_folder,
            exist_ok=True
        )

        filename = url.split("/")[-1]

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        save_path = os.path.join(
            save_folder,
            filename
        )

        if os.path.exists(save_path):

            print(
                f"Already exists: {filename}"
            )

            return save_path

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"Failed: {url}"
            )

            return None

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

        if "pdf" not in content_type.lower():

            print(
                f"Not PDF: {url}"
            )

            return None

        with open(
            save_path,
            "wb"
        ) as f:

            f.write(
                response.content
            )

        print(
            f"Downloaded: {filename}"
        )

        return save_path

    except Exception as e:

        print(
            "Download Failed:",
            e
        )

        return None