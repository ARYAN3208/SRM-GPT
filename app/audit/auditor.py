from pathlib import Path
import json
from datetime import datetime

from website_auditor import audit_website
from pdf_auditor import audit_pdfs
from ocr_auditor import audit_ocr
from rag_auditor import audit_rag
from report_generator import generate_report

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 80)
    print("SRM DATASET AUDITOR")
    print("=" * 80)

    report = {
        "generated_at": datetime.now().isoformat(),
        "website": audit_website(),
        "pdf": audit_pdfs(),
        "ocr": audit_ocr(),
        "rag": audit_rag(),
    }

    report["summary"] = {
        "website_coverage": report["website"].get("coverage", 0),
        "pdf_coverage": report["pdf"].get("coverage", 0),
        "ocr_coverage": report["ocr"].get("coverage", 0),
        "rag_score": report["rag"].get("score", 0),
    }

    json_report = REPORT_DIR / "audit_report.json"

    with open(json_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    generate_report(report, REPORT_DIR)

    print("\nAudit Completed\n")

    print(f"Website Coverage : {report['summary']['website_coverage']:.2f}%")
    print(f"PDF Coverage     : {report['summary']['pdf_coverage']:.2f}%")
    print(f"OCR Coverage     : {report['summary']['ocr_coverage']:.2f}%")
    print(f"RAG Score        : {report['summary']['rag_score']:.2f}/100")

    print("\nReports Generated")
    print(json_report)
    print(REPORT_DIR / "audit_report.txt")


if __name__ == "__main__":
    main()
