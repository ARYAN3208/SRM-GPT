import os
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def download_images_from_page(
    url,
    save_folder
):

    os.makedirs(
        save_folder,
        exist_ok=True
    )

    options = Options()

    options.add_argument(
        "--headless"
    )

    options.add_argument(
        "--disable-gpu"
    )

    driver = webdriver.Chrome(
        options=options
    )

    downloaded = []

    try:

        driver.get(url)

        driver.implicitly_wait(
            5
        )

        images = driver.find_elements(
            By.TAG_NAME,
            "img"
        )

        print(
            f"Images found: {len(images)}"
        )

        for img in images:

            src = img.get_attribute(
                "src"
            )

            if not src:
                continue

            lower = src.lower()

            if not any(
                ext in lower
                for ext in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                ]
            ):
                continue

            filename = (
                src.split("/")[-1]
                .split("?")[0]
            )

            if not filename:
                continue

            save_path = os.path.join(
                save_folder,
                filename
            )

            if os.path.exists(
                save_path
            ):
                continue

            try:

                response = requests.get(
                    src,
                    timeout=20
                )

                if response.status_code == 200:

                    with open(
                        save_path,
                        "wb"
                    ) as f:

                        f.write(
                            response.content
                        )

                    downloaded.append(
                        save_path
                    )

                    print(
                        f"Downloaded: {filename}"
                    )

            except Exception:
                pass

    finally:

        driver.quit()

    return downloaded