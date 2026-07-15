from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "literature.json"
TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"


def strip_publisher_notice(text: str) -> str:
    return re.sub(
        r"\s*(?:(?:Copyright|版权所有)\s*)?©\s*\d{4}.*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


def source_fingerprint(title: str, abstract: str) -> str:
    value = f"{title}\n{abstract}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def split_text(text: str, limit: int = 1800) -> list[str]:
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(sentence[i : i + limit] for i in range(0, len(sentence), limit))
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > limit:
            chunks.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def translate_chunk(text: str) -> str:
    params = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text,
        }
    )
    request = urllib.request.Request(
        f"{TRANSLATE_URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return "".join(part[0] for part in payload[0] if part and part[0]).strip()


def translate_text(text: str) -> str:
    if not text.strip():
        return ""
    translated: list[str] = []
    for chunk in split_text(text.strip()):
        last_error: Exception | None = None
        for delay in (0, 2, 6):
            if delay:
                time.sleep(delay)
            try:
                translated.append(translate_chunk(chunk))
                time.sleep(0.15)
                break
            except Exception as error:  # Network failures are retried and then surfaced.
                last_error = error
        else:
            raise RuntimeError(f"Translation failed after retries: {last_error}")
    return " ".join(translated)


def is_legacy_summary(value: str) -> bool:
    return not value or value.startswith("本文与") or "PubMed 摘要显示" in value


def translate_item(index: int, item: dict) -> tuple[int, str, str]:
    title_zh = item.get("titleZh", "")
    summary_zh = item.get("summaryZh", "")
    if not title_zh:
        title_zh = translate_text(item.get("title", ""))
    if is_legacy_summary(summary_zh):
        abstract = item.get("abstractEn", "").strip()
        summary_zh = translate_text(abstract) if abstract else "PubMed 未提供可翻译的摘要。"
    return index, title_zh, summary_zh


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Translate at most N records; 0 means all.")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent translation workers.")
    args = parser.parse_args()

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    pending: list[tuple[int, dict]] = []
    for index, item in enumerate(data.get("items", [])):
        item["abstractEn"] = strip_publisher_notice(item.get("abstractEn", ""))
        item["summaryZh"] = strip_publisher_notice(item.get("summaryZh", ""))
        abstract = item.get("abstractEn", "").strip()
        item["translationSource"] = source_fingerprint(item.get("title", ""), abstract)
        needs_title = not item.get("titleZh")
        needs_abstract = is_legacy_summary(item.get("summaryZh", ""))
        if needs_title or needs_abstract:
            pending.append((index, dict(item)))

    if args.limit:
        pending = pending[: args.limit]

    translated_count = 0
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(translate_item, index, item): (index, item.get("doi", ""))
            for index, item in pending
        }
        for future in as_completed(futures):
            original_index, doi = futures[future]
            try:
                index, title_zh, summary_zh = future.result()
            except Exception as error:
                errors.append(f"{doi}: {error}")
                print(f"[{original_index + 1}/{len(data['items'])}] {doi} failed: {error}", flush=True)
                continue

            data["items"][index]["titleZh"] = title_zh
            data["items"][index]["summaryZh"] = summary_zh
            translated_count += 1
            if translated_count % 5 == 0:
                DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"[{index + 1}/{len(data['items'])}] {doi} translated", flush=True)

    data["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Translated {translated_count} records")
    if errors:
        raise RuntimeError(f"{len(errors)} translations failed; first error: {errors[0]}")


if __name__ == "__main__":
    main()
