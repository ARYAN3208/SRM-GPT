from pathlib import Path

PDF_FOLDER = Path(
    "app/05_data/uploads"
)

PDF_ALIASES = {

    "fee": [
        "prospectus",
        "engineering",
        "technology"
    ],

    "fees": [
        "prospectus",
        "engineering",
        "technology"
    ],

    "btech": [
        "engineering",
        "technology",
        "prospectus"
    ],

    "hostel": [
        "hall"
    ],

    "scholarship": [
        "scholarships"
    ],

    "admission": [
        "admission",
        "prospectus"
    ],

    "prospectus": [
        "prospectus"
    ]

}

def find_pdf(query):

    query = query.lower()

    pdfs = []

    for pdf in PDF_FOLDER.glob("*.pdf"):

        filename = pdf.name.lower()

        score = 0

        for word in query.split():

            if word in filename:

                score += 5

            aliases = PDF_ALIASES.get(
                word,
                []
            )

            for alias in aliases:

                if alias in filename:

                    score += 3

        pdfs.append(
            (score, pdf)
        )

    pdfs.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    if not pdfs:

        return None

    best_score = pdfs[0][0]

    if best_score <= 0:

        return None

    return str(
        pdfs[0][1]
    )