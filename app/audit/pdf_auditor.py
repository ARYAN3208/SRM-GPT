from pathlib import Path

from utils import (
    RAW_DIR,
    UPLOADS_DIR,
    load_json,
    percentage
)

PDF_DATA_FILE = RAW_DIR / "ktr_pdf_data.json"


def get_downloaded_pdfs():
    if not UPLOADS_DIR.exists():
        return set()

    pdfs = set()

    for pdf in UPLOADS_DIR.rglob("*.pdf"):
        pdfs.add(pdf.name.lower())

    return pdfs


def audit_pdfs():
    print("\nAuditing PDFs...")

    records = load_json(PDF_DATA_FILE)

    parsed = 0
    empty = 0
    corrupted = 0
    duplicate = 0

    pdf_urls = set()
    duplicate_urls = set()

    for record in records:

        if not isinstance(record, dict):
            continue

        url = record.get("url", "").strip()

        if url:

            if url in pdf_urls:
                duplicate_urls.add(url)
                duplicate += 1
            else:
                pdf_urls.add(url)

        parsed += 1

        pages = record.get("pages", [])

        if pages:

            extracted = []

            for page in pages:

                if not isinstance(page, dict):
                    continue

                text = page.get("text", "").strip()

                if text:
                    extracted.append(text)

            full_text = " ".join(extracted)

        else:

            full_text = (
                record.get("text", "")
                or record.get("content", "")
            ).strip()

        if not full_text:
            empty += 1
            continue

        if len(full_text) < 20:
            corrupted += 1
            continue

    downloaded = get_downloaded_pdfs()

    parsed_names = set()

    for record in records:

        if not isinstance(record, dict):
            continue

        file_name = record.get("file", "").strip()

        if file_name:
            parsed_names.add(Path(file_name).name.lower())

    missing_downloads = sorted(
        downloaded - parsed_names
    )

    coverage = percentage(
        len(parsed_names),
        len(downloaded)
    )

    print(f"Downloaded PDFs    : {len(downloaded)}")
    print(f"Parsed PDFs        : {parsed}")
    print(f"Coverage           : {coverage}%")
    print(f"Duplicate PDFs     : {duplicate}")
    print(f"Empty PDFs         : {empty}")
    print(f"Corrupted PDFs     : {corrupted}")
    print(f"Missing Parsed     : {len(missing_downloads)}")

    return {
        "coverage": coverage,
        "downloaded_pdfs": len(downloaded),
        "parsed_pdfs": parsed,
        "duplicate_pdfs": duplicate,
        "empty_pdfs": empty,
        "corrupted_pdfs": corrupted,
        "missing_parsed": len(missing_downloads),
        "missing_parsed_list": missing_downloads,
        "duplicate_url_list": sorted(duplicate_urls)
    }