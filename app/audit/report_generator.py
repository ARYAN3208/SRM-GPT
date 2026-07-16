from pathlib import Path


def generate_report(report, report_dir):
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / "audit_report.txt"

    with open(report_file, "w", encoding="utf-8") as f:

        f.write("=" * 80 + "\n")
        f.write("SRM DATASET AUDIT REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Generated At : {report['generated_at']}\n\n")

        website = report["website"]

        f.write("WEBSITE AUDIT\n")
        f.write("-" * 80 + "\n")
        f.write(f"Coverage           : {website['coverage']}%\n")
        f.write(f"Live URLs          : {website['live_urls']}\n")
        f.write(f"Scraped URLs       : {website['scraped_urls']}\n")
        f.write(f"Missing URLs       : {website['missing_urls']}\n")
        f.write(f"Duplicate URLs     : {website['duplicate_urls']}\n")
        f.write(f"Empty Pages        : {website['empty_pages']}\n")
        f.write(f"Error Pages        : {website['error_pages']}\n\n")

        pdf = report["pdf"]

        f.write("PDF AUDIT\n")
        f.write("-" * 80 + "\n")
        f.write(f"Coverage           : {pdf['coverage']}%\n")
        f.write(f"Downloaded PDFs    : {pdf['downloaded_pdfs']}\n")
        f.write(f"Parsed PDFs        : {pdf['parsed_pdfs']}\n")
        f.write(f"Duplicate PDFs     : {pdf['duplicate_pdfs']}\n")
        f.write(f"Empty PDFs         : {pdf['empty_pdfs']}\n")
        f.write(f"Corrupted PDFs     : {pdf['corrupted_pdfs']}\n")
        f.write(f"Missing Parsed     : {pdf['missing_parsed']}\n\n")

        ocr = report["ocr"]

        f.write("OCR AUDIT\n")
        f.write("-" * 80 + "\n")
        f.write(f"Coverage           : {ocr['coverage']}%\n")
        f.write(f"Searchable PDFs    : {ocr['searchable_pdfs']}\n")
        f.write(f"Scanned PDFs       : {ocr['scanned_pdfs']}\n")
        f.write(f"OCR Completed      : {ocr['ocr_completed']}\n")
        f.write(f"OCR Missing        : {ocr['ocr_missing']}\n")
        f.write(f"Missing PDF Files  : {ocr['missing_pdf_files']}\n\n")

        rag = report["rag"]

        f.write("RAG AUDIT\n")
        f.write("-" * 80 + "\n")
        f.write(f"Dataset Score      : {rag['score']}/100\n")
        f.write(f"Total Chunks       : {rag['total_chunks']}\n")
        f.write(f"Duplicate Chunks   : {rag['duplicate_chunks']}\n")
        f.write(f"Duplicate IDs      : {rag['duplicate_chunk_ids']}\n")
        f.write(f"Empty Chunks       : {rag['empty_chunks']}\n")
        f.write(f"Small Chunks       : {rag['small_chunks']}\n")
        f.write(f"Large Chunks       : {rag['large_chunks']}\n")
        f.write(f"Missing Metadata   : {rag['missing_metadata']}\n")
        f.write(f"Average Length     : {rag['average_chunk_length']:.2f}\n\n")

        f.write("SOURCE DISTRIBUTION\n")
        f.write("-" * 80 + "\n")

        for source, count in rag["sources"].items():
            f.write(f"{source:<30}{count}\n")

        f.write("\n")

        summary = report["summary"]

        f.write("=" * 80 + "\n")
        f.write("OVERALL SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Website Coverage : {summary['website_coverage']:.2f}%\n")
        f.write(f"PDF Coverage     : {summary['pdf_coverage']:.2f}%\n")
        f.write(f"OCR Coverage     : {summary['ocr_coverage']:.2f}%\n")
        f.write(f"RAG Score        : {summary['rag_score']:.2f}/100\n")