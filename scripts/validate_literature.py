from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "literature.json"
SITE_PATH = ROOT / "site" / "index.html"
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
REQUIRED_DOIS = {
    "10.1038/s41586-020-2545-9",
    "10.1016/j.cell.2026.01.018",
}


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if not items:
        raise SystemExit("No literature records found")

    seen: set[str] = set()
    for item in items:
        doi = item.get("doi", "").strip()
        if not DOI_PATTERN.match(doi):
            raise SystemExit(f"Invalid DOI: {doi!r}")
        if doi.lower() in seen:
            raise SystemExit(f"Duplicate DOI: {doi}")
        seen.add(doi.lower())

        if item.get("doiUrl") != f"https://doi.org/{doi}":
            raise SystemExit(f"DOI URL mismatch: {doi}")
        pubmed_url = item.get("pubmedUrl", "")
        if urlparse(pubmed_url).netloc != "pubmed.ncbi.nlm.nih.gov":
            raise SystemExit(f"Invalid PubMed URL: {pubmed_url}")
        if not item.get("titleZh"):
            raise SystemExit(f"Missing Chinese title: {doi}")
        if not item.get("summaryZh"):
            raise SystemExit(f"Missing Chinese abstract: {doi}")
        if not item.get("matchedTerms") or "待人工复核" in item.get("categories", []):
            raise SystemExit(f"Missing explicit inclusion keyword: {doi}")

    missing_required = REQUIRED_DOIS - seen
    if missing_required:
        raise SystemExit(f"Missing required landmark DOI(s): {', '.join(sorted(missing_required))}")

    html_text = SITE_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="literature-data" type="application/json">(.*?)</script>',
        html_text,
        re.DOTALL,
    )
    if not match:
        raise SystemExit("Embedded literature JSON was not found in site/index.html")
    embedded = json.loads(match.group(1))
    if len(embedded.get("items", [])) != len(items):
        raise SystemExit("Website record count does not match data/literature.json")

    print(f"Validated {len(items)} records")


if __name__ == "__main__":
    main()
