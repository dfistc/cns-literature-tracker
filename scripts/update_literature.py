from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "literature.json"
NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

JOURNALS = [
    "Cell",
    "Molecular Cell",
    "Cell Chemical Biology",
    "Cell Systems",
    "Cell Reports",
    "Cell Reports Methods",
    "Cell Genomics",
    "Cell Host & Microbe",
    "Developmental Cell",
    "Cancer Cell",
    "Cell Stem Cell",
    "Nature",
    "Nature Biotechnology",
    "Nature Chemical Biology",
    "Nature Methods",
    "Nature Communications",
    "Nature Biomedical Engineering",
    "Nature Nanotechnology",
    "Nature Medicine",
    "Nature Cell Biology",
    "Nature Structural & Molecular Biology",
    "Nature Genetics",
    "Nature Metabolism",
    "Nature Microbiology",
    "Science",
    "Science Advances",
    "Science Translational Medicine",
    "Science Signaling",
    "Science Robotics",
    "Science Immunology",
]
JOURNAL_ALIASES = {
    "Science": ["Science", "Science (New York, N.Y.)"],
}
JOURNAL_CANONICAL = {
    alias.casefold(): canonical
    for canonical in JOURNALS
    for alias in JOURNAL_ALIASES.get(canonical, [canonical])
}

# These user-identified landmarks double as regression guards for the search.
LANDMARK_PMIDS = ["32728216", "41861782"]
LANDMARK_DOIS = ["10.1038/s41586-020-2545-9", "10.1016/j.cell.2026.01.018"]

TAC_FAMILY_TERMS = [
    "protac",
    "proteolysis-targeting chimera",
    "proteolysis targeting chimera",
    "lytac",
    "lysosome-targeting chimera",
    "lysosome-targeting chimaera",
    "autac",
    "autophagy-targeting chimera",
    "attec",
    "autophagosome-tethering compound",
    "abtac",
    "antibody-based protac",
    "kinetac",
    "transtac",
    "dubtac",
    "ribotac",
    "photac",
    "cliptac",
    "o'protac",
    "bioprotac",
    "traftac",
    "bacprotac",
    "protab",
    "mode-a",
    "cma-tac",
    "gluetac",
    "endtac",
    "haloprotac",
]

TPD_CONCEPT_TERMS = [
    "targeted protein degradation",
    "targeted degradation",
    "induced protein degradation",
    "protein degrader",
    "molecular glue degrader",
    "molecular glue",
    "degron",
    "trim-away",
    "extracellular targeted protein degradation",
    "erad-engaging chimera",
    "erad-targeting",
    "eradec",
]

CATEGORY_RULES = {
    "合成生物学": [
        "synthetic biology",
        "synthetic circuit",
        "synthetic gene circuit",
        "genetic circuit",
        "gene circuit",
        "engineered bacteria",
        "genome writing",
        "synthetic genome",
        "cell-free system",
        "programmable cell",
        "designer receptor",
    ],
    "靶向蛋白降解": [
        *TPD_CONCEPT_TERMS,
        *TAC_FAMILY_TERMS,
    ],
    "溶酶体/蛋白酶体": [
        "lysosome",
        "lysosomal",
        "endolysosomal",
        "proteasome",
        "ubiquitin-proteasome",
        "ubiquitin proteasome",
        "proteostasis",
        "ER-associated degradation",
        "autophagy",
        "endosome",
    ],
}


def fetch_text(url: str, params: dict[str, str | int]) -> str:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{url}?{query}",
        headers={"User-Agent": "cns-literature-tracker/1.0 (mailto:research@example.com)"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8")


def journal_query() -> str:
    names = [
        alias
        for canonical in JOURNALS
        for alias in JOURNAL_ALIASES.get(canonical, [canonical])
    ]
    return " OR ".join(f'"{name}"[journal]' for name in names)


def keyword_query() -> str:
    terms = sorted({term for terms in CATEGORY_RULES.values() for term in terms})
    return " OR ".join(f'"{term}"[tiab]' if " " in term else f"{term}[tiab]" for term in terms)


def targeted_degradation_query() -> str:
    terms = sorted(set(TPD_CONCEPT_TERMS + TAC_FAMILY_TERMS))
    explicit = [f'"{term}"[tiab]' for term in terms]
    # TACs alone is ambiguous, so require degradation/chimera context.
    contextual_tacs = (
        '"TACs"[tiab] AND '
        '(degrad*[tiab] OR degrader*[tiab] OR chimera*[tiab] OR chimaera*[tiab])'
    )
    return " OR ".join(explicit + [f"({contextual_tacs})"])


def search_one(term: str, retmax: int) -> list[str]:
    payload = fetch_text(
        f"{NCBI_BASE}/esearch.fcgi",
        {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": retmax,
            "sort": "pub date",
        },
    )
    data = json.loads(payload)
    return data.get("esearchresult", {}).get("idlist", [])


def search_pmids(retmax: int, tpd_retmax: int) -> list[str]:
    pmids: list[str] = list(LANDMARK_PMIDS)
    current_year = datetime.now(timezone.utc).year
    for year in range(current_year, 2019, -1):
        base = f"({journal_query()}) AND ({year}[dp])"
        pmids.extend(search_one(f"{base} AND ({keyword_query()})", retmax))
        time.sleep(0.34)
        pmids.extend(
            search_one(
                f"{base} AND ({targeted_degradation_query()})",
                tpd_retmax,
            )
        )
        time.sleep(0.34)
    return list(dict.fromkeys(pmids))


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def node_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return clean_text(" ".join(node.itertext()))


def article_year(article: ET.Element) -> int | None:
    for path in [
        ".//JournalIssue/PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubMedPubDate[@PubStatus='pubmed']/Year",
    ]:
        text = node_text(article.find(path))
        if text.isdigit():
            return int(text)
    medline_date = node_text(article.find(".//JournalIssue/PubDate/MedlineDate"))
    match = re.search(r"(20\d{2})", medline_date)
    return int(match.group(1)) if match else None


def article_date(article: ET.Element) -> str:
    year = article_year(article)
    month = node_text(article.find(".//JournalIssue/PubDate/Month")) or "01"
    day = node_text(article.find(".//JournalIssue/PubDate/Day")) or "01"
    month_map = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    month = month_map.get(month[:3], month)
    if year is None:
        return ""
    return f"{year:04d}-{int(month):02d}-{int(day):02d}" if month.isdigit() and day.isdigit() else str(year)


def doi_for(article: ET.Element) -> str:
    for item in article.findall(".//ArticleId"):
        if item.attrib.get("IdType") == "doi":
            return node_text(item)
    return ""


def classify(title: str, abstract: str) -> list[str]:
    haystack = f"{title} {abstract}".lower()
    categories = [
        category
        for category, terms in CATEGORY_RULES.items()
        if any(term.lower() in haystack for term in terms)
    ]
    if has_contextual_tacs(haystack) and "靶向蛋白降解" not in categories:
        categories.append("靶向蛋白降解")
    return categories


def has_contextual_tacs(haystack: str) -> bool:
    return bool(
        re.search(r"\btacs\b", haystack, flags=re.IGNORECASE)
        and re.search(
            r"\b(?:degrad\w*|chim(?:era|aera)s?)\b",
            haystack,
            flags=re.IGNORECASE,
        )
    )


def matched_terms(title: str, abstract: str) -> list[str]:
    haystack = f"{title} {abstract}".lower()
    matches: list[str] = []
    for terms in CATEGORY_RULES.values():
        for term in terms:
            if term.lower() in haystack and term not in matches:
                matches.append(term)
    if has_contextual_tacs(haystack):
        matches.append("TACs + degradation/chimera context")
    return matches[:8]


def abstract_for_translation(abstract: str) -> str:
    """Remove publisher boilerplate that is not part of the scientific abstract."""
    return re.sub(
        r"\s*(?:Copyright\s+)?©\s*\d{4}.*?(?:All rights reserved\.)?\s*$",
        "",
        abstract,
        flags=re.IGNORECASE,
    ).strip()


def text_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def parse_articles(xml_text: str, previous: dict[str, dict]) -> list[dict]:
    root = ET.fromstring(xml_text)
    records: list[dict] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = node_text(article.find(".//PMID"))
        title = node_text(article.find(".//ArticleTitle"))
        journal_raw = node_text(article.find(".//Journal/Title"))
        journal = JOURNAL_CANONICAL.get(journal_raw.casefold(), "")
        doi = doi_for(article)
        year = article_year(article)
        abstract = node_text(article.find(".//Abstract"))
        if not pmid or not title or not doi or not year or year < 2020:
            continue
        if doi.startswith("10.1038/d41586") or title.lower().startswith(
            ("author correction", "publisher correction", "correction", "erratum", "retraction")
        ):
            continue
        if not journal:
            continue
        categories = classify(title, abstract)
        terms = matched_terms(title, abstract)
        if not categories or not terms:
            continue
        prior = previous.get(doi.lower(), {})
        clean_abstract = abstract_for_translation(abstract)
        source_fingerprint = text_fingerprint(f"{title}\n{clean_abstract}")
        translation_current = prior.get("translationSource") == source_fingerprint
        records.append(
            {
                "pmid": pmid,
                "title": title,
                "titleZh": prior.get("titleZh", "") if translation_current else "",
                "journal": journal,
                "year": year,
                "published": article_date(article),
                "doi": doi,
                "doiUrl": f"https://doi.org/{doi}",
                "pubmedUrl": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "categories": categories,
                "matchedTerms": terms,
                "standard": f"2020 年以来；期刊属于 CNS 正刊或 Cell/Nature/Science 系列子刊；题名/摘要命中：{', '.join(terms) if terms else '关键词待复核'}。",
                "abstractEn": clean_abstract,
                "summaryZh": prior.get("summaryZh", "") if translation_current else "",
                "translationSource": source_fingerprint,
            }
        )
    records.sort(key=lambda row: (row["year"], row["published"], row["journal"]), reverse=True)
    return records


def fetch_records(retmax: int, tpd_retmax: int) -> list[dict]:
    pmids = search_pmids(retmax, tpd_retmax)
    if not pmids:
        return []
    previous = {}
    if DATA_PATH.exists():
        old = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        previous = {item["doi"].lower(): item for item in old.get("items", []) if item.get("doi")}
    records: list[dict] = []
    for offset in range(0, len(pmids), 80):
        batch = pmids[offset : offset + 80]
        xml_text = fetch_text(
            f"{NCBI_BASE}/efetch.fcgi",
            {"db": "pubmed", "id": ",".join(batch), "retmode": "xml"},
        )
        records.extend(parse_articles(xml_text, previous))
        time.sleep(0.34)
    seen: set[str] = set()
    unique = []
    for record in records:
        key = record["doi"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(record)
    unique.sort(key=lambda row: (row["year"], row["published"], row["journal"]), reverse=True)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retmax", type=int, default=120)
    parser.add_argument("--tpd-retmax", type=int, default=1000)
    args = parser.parse_args()

    records = fetch_records(args.retmax, args.tpd_retmax)
    found_dois = {record["doi"].lower() for record in records}
    missing_landmarks = [doi for doi in LANDMARK_DOIS if doi.lower() not in found_dois]
    if missing_landmarks:
        raise RuntimeError(f"Required landmark articles are missing: {', '.join(missing_landmarks)}")
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    DATA_PATH.write_text(
        json.dumps(
            {
                "updatedAt": now,
                "source": "PubMed E-utilities / NCBI",
                "scope": "2020 年以来；CNS 正刊及 Cell/Nature/Science 系列子刊；合成生物学、靶向蛋白降解、溶酶体或蛋白酶体相关关键词。",
                "items": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} records to {DATA_PATH}")
    time.sleep(0.34)


if __name__ == "__main__":
    main()
