import re

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

def create_chunks(text):

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"www\.\S+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = text.strip()

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=800,

        chunk_overlap=150,

        separators=[
            "\n\n",
            "\n",
            ". ",
            ", ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_text(
        text
    )

    chunks = [

        chunk.strip()

        for chunk in chunks

        if len(chunk.strip()) > 100

    ]

    return chunks