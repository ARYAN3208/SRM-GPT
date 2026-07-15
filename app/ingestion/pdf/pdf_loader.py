import fitz

def load_pdf(pdf_path):

    try:
        doc = fitz.open(pdf_path)
        return doc

    except Exception as e:
        print("PDF Load Error:", e)
        return None