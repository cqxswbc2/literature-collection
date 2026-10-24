"""Identify downloaded PDFs, verify them against manifest.csv, and file them by journal.

Identification order (first hit wins; a file matching two rows is reported, never moved):
  1. DOI in XMP metadata (prism:doi / pdfx:doi)        - most reliable
  2. a manifest DOI printed on page 1-2                 - needs PyMuPDF
  3. the row's match_phrase on page 1-2 (spaces/punctuation ignored) - for CNKI papers without DOI
Never trust "the first DOI found in the file": it is often a reference.

Target layout under --dest:
  英文/<folder or source>/<year>_<first_author>_<short_title>.pdf
  中文/期刊论文/...   or   中文/学位论文/...（硕士|博士）.pdf

Default is a dry run. Add --apply to move files and write status/file back to the manifest.
Unmatched files are only counted, not listed (they are usually the user's private files);
use --show-unmatched when debugging on your own data.

Usage:
  python archive_pdfs.py manifest.csv --src "D:\\Downloads" --dest "已下载论文" --since-hours 48
  python archive_pdfs.py manifest.csv --src "D:\\Downloads" --dest "已下载论文" --since-hours 48 --apply
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except ImportError:  # still works with XMP-only matching
    fitz = None

MIN_PDF_BYTES = 60_000
XMP_DOI = re.compile(rb"(?:prism:doi|pdfx:doi)>\s*(10\.\d{4,9}/[^<\s]+)\s*<", re.I)
THESIS_SUFFIX = {"master": "（硕士）", "phd": "（博士）"}


@dataclass(frozen=True)
class Match:
    path: str
    row_index: int
    how: str
    pages: int


def read_manifest(path: str) -> tuple[list[dict], list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_manifest(path: str, rows: list[dict], fields: list[str]) -> None:
    extra = [k for r in rows for k in r if k not in fields]
    fields = fields + list(dict.fromkeys(extra))
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def squash(text: str) -> str:
    """Lower-case and drop everything except letters/digits (keeps CJK)."""
    return re.sub(r"[\W_]+", "", text.lower())


def safe_name(text: str, limit: int = 80) -> str:
    text = re.sub(r'[\\/:*?"<>|\r\n\t]', " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit].rstrip(" .")


def target_path(dest: str, row: dict) -> str:
    title = safe_name(row.get("short_title") or "untitled")
    name = f"{row.get('year', '')}_{safe_name(row.get('first_author', ''), 30)}_{title}"
    if row.get("lang") == "zh":
        kind = row.get("kind", "journal")
        sub = os.path.join("中文", "学位论文" if kind in THESIS_SUFFIX else "期刊论文")
        name += THESIS_SUFFIX.get(kind, "")
    else:
        sub = os.path.join("英文", safe_name(row.get("folder") or row.get("source") or "Other", 60))
    return os.path.join(dest, sub, name + ".pdf")


def page_text(path: str) -> tuple[str, int]:
    if fitz is None:
        return "", 0
    try:
        with fitz.open(path) as doc:
            text = " ".join(doc[i].get_text() for i in range(min(2, doc.page_count)))
            return squash(text), doc.page_count
    except Exception:
        return "", 0


def identify(path: str, rows: list[dict]) -> tuple[list[Match], str]:
    """Return candidate matches for one PDF and a status string."""
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(b"%PDF") or len(data) < MIN_PDF_BYTES:
        return [], "not-a-real-pdf"
    xmp = {m.group(1).decode("ascii", "ignore").lower() for m in XMP_DOI.finditer(data)}
    text, pages = page_text(path)
    hits: list[Match] = []
    for i, row in enumerate(rows):
        doi = (row.get("doi") or "").strip().lower()
        if doi and doi in xmp:
            hits.append(Match(path, i, "xmp-doi", pages))
        elif doi and text and squash(doi) in text:
            hits.append(Match(path, i, "doi-on-page", pages))
        elif row.get("match_phrase") and text and squash(row["match_phrase"]) in text:
            hits.append(Match(path, i, "title-phrase", pages))
    # an XMP hit beats weaker evidence for other rows
    strong = [h for h in hits if h.how == "xmp-doi"]
    return (strong or hits), "ok"


def recent_pdfs(src: str, since_hours: float) -> list[str]:
    cutoff = time.time() - since_hours * 3600
    out = []
    for name in os.listdir(src):
        path = os.path.join(src, name)
        if name.lower().endswith(".pdf") and os.path.isfile(path) and os.path.getmtime(path) >= cutoff:
            out.append(path)
    return sorted(out, key=os.path.getmtime)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--src", required=True, help="folder the browser downloads into")
    ap.add_argument("--dest", required=True, help="archive root, e.g. 已下载论文")
    ap.add_argument("--since-hours", type=float, default=72, help="only look at files this recent")
    ap.add_argument("--apply", action="store_true", help="actually move files and update the manifest")
    ap.add_argument("--show-unmatched", action="store_true", help="print names of unmatched PDFs")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    if fitz is None:
        print("note: PyMuPDF not installed (pip install pymupdf); only XMP DOIs can be matched\n")
    rows, fields = read_manifest(args.manifest)
    for col in ("status", "file"):
        if col not in fields:
            fields.append(col)

    moved = dup = ambiguous = junk = 0
    unmatched: list[str] = []
    claimed: set[int] = set()
    for path in recent_pdfs(args.src, args.since_hours):
        matches, status = identify(path, rows)
        if status != "ok":
            junk += 1
            continue
        if not matches:
            unmatched.append(os.path.basename(path))
            continue
        if len({m.row_index for m in matches}) > 1:
            ambiguous += 1
            ids = ", ".join(rows[m.row_index].get("id", "?") for m in matches)
            print(f"AMBIGUOUS  {os.path.basename(path)[:50]}  -> rows {ids} (not moved)")
            continue
        m = matches[0]
        row = rows[m.row_index]
        dst = target_path(args.dest, row)
        rel = os.path.relpath(dst, args.dest)
        if os.path.exists(dst) or m.row_index in claimed:
            dup += 1
            print(f"DUPLICATE  {os.path.basename(path)[:50]}  (already have {rel})")
            continue
        claimed.add(m.row_index)
        print(f"{'MOVE' if args.apply else 'WOULD MOVE'}  [{m.how}, {m.pages}p]  "
              f"{os.path.basename(path)[:45]}  ->  {rel}")
        if args.apply:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(path, dst)
            row["status"] = "downloaded"
            row["file"] = rel.replace(os.sep, "/")
            moved += 1

    print(f"\nmatched {len(claimed)}, moved {moved}, duplicates {dup}, ambiguous {ambiguous}, "
          f"not-a-real-pdf {junk}, unmatched {len(unmatched)}")
    if args.show_unmatched:
        for name in unmatched:
            print("  unmatched:", name)
    if args.apply:
        write_manifest(args.manifest, rows, fields)
        print("manifest updated:", args.manifest)
    else:
        print("dry run - add --apply to move files")


if __name__ == "__main__":
    main()
