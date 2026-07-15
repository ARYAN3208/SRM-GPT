def build_metadata(chunk):

    source = chunk.get(
        "source",
        ""
    )

    source_type = "unknown"

    if "website" in source:

        source_type = "website"

    elif "pdf" in source:

        source_type = "pdf"

    elif "ocr" in source:

        source_type = "ocr"

    metadata = {

        "campus":
        "SRM_KTR",

        "source_type":
        source_type,

        "source":
        source,

        "chunk_id":
        chunk.get(
            "chunk_id",
            -1
        )

    }

    return metadata