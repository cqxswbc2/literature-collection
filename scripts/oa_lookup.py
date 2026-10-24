"""Look up open-access copies for papers in manifest.csv and optionally download them.

For every row that is not yet downloaded:
  1. If the DOI is empty, try to fill it from OpenAlex using `short_title` / `match_phrase`
     (the row's note is marked "doi-from-openalex: please check").
  2. Ask OpenAlex (is_oa, best pdf url) and Unpaywall (repository copies) for OA locations.
  3. Write `oa` and `oa_urls` columns back to the manifest.
  4. With --download DIR: try each candidate, keep only real PDFs (> 60 KB, %PDF header),
     save as DIR/<doi-safe>.pdf. Identity is NOT verified here - run archive_pdfs.py next.

Elsevier/ScienceDirect URLs are skipped on purpose: they answer scripts with 403 or a bot check.

Usage:
  python oa_lookup.py manifest.csv --email you@example.com
  python oa_lookup.py manifest.csv --email you@example.com --download staging
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import socket
import sys
import time
import urllib.parse
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept": "text/html,application/pdf,*/*",
}
BLOCKED_HOSTS = ("sciencedirect.com", "elsevier.com", "sciencedirectassets.com", "nature.com")
# preprint servers: title/content can differ from the published paper, so never use them as the full text
PREPRINT_HOSTS = ("researchsquare.com", "preprints.org", "authorea.com")
MIN_PDF_BYTES = 60_000


def read_manifest(path: str) -> tuple[list[dict], list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_manifest(path: str, rows: list[dict], fields: list[str]) -> None:
    # rows may have gained columns (e.g. source/year filled from OpenAlex); keep them all
    extra = [k for r in rows for k in r if k not in fields]
    fields = fields + list(dict.fromkeys(extra))
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def get_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "literature-collection/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch(url: str, timeout: int = 40) -> tuple[bytes, str]:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as resp:
        return resp.read(), resp.geturl()


def is_blocked(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    return any(h in host for h in BLOCKED_HOSTS + PREPRINT_HOSTS)


def is_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF") and len(data) > MIN_PDF_BYTES


def fill_doi_from_title(row: dict, email: str) -> None:
    query = row.get("match_phrase") or row.get("short_title") or ""
    query = re.sub(r"[^\w\s-]", " ", query).strip()
    if not query:
        return
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(query)
           + f"&per_page=5&mailto={urllib.parse.quote(email)}")
    for work in get_json(url).get("results", []):
        source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        if re.search(r"National Bureau|RePEc|SSRN|ICPSR", source):
            continue  # prefer the journal record over working-paper mirrors
        doi = (work.get("doi") or "").replace("https://doi.org/", "")
        if doi:
            row["doi"] = doi
            row["year"] = row.get("year") or str(work.get("publication_year") or "")
            row["source"] = row.get("source") or source
            row["note"] = (row.get("note", "") + " doi-from-openalex: please check").strip()
        return


def oa_candidates(doi: str, email: str) -> tuple[bool, list[tuple[str, str]]]:
    """Return (is_oa, ordered list of (kind, url)) with blocked hosts removed."""
    urls, is_oa = [], False
    try:
        work = get_json(f"https://api.openalex.org/works/https://doi.org/{doi}?mailto={urllib.parse.quote(email)}")
        is_oa = bool((work.get("open_access") or {}).get("is_oa"))
        for loc in [work.get("best_oa_location")] + (work.get("locations") or []):
            if loc and loc.get("pdf_url"):
                urls.append(("pdf", loc["pdf_url"]))
    except Exception as exc:  # OpenAlex outage should not stop Unpaywall
        print(f"  openalex error for {doi}: {exc}")
    try:
        up = get_json(f"https://api.unpaywall.org/v2/{doi}?email={urllib.parse.quote(email)}")
        is_oa = is_oa or bool(up.get("is_oa"))
        for loc in up.get("oa_locations") or []:
            if loc.get("url_for_pdf"):
                urls.append(("pdf", loc["url_for_pdf"]))
            if loc.get("host_type") == "repository" and loc.get("url"):
                urls.append(("page", loc["url"]))
    except Exception as exc:
        print(f"  unpaywall error for {doi}: {exc}")
    seen, ordered = set(), []
    for kind, url in urls:
        if url not in seen and not is_blocked(url):
            seen.add(url)
            ordered.append((kind, url))
    return is_oa, ordered


def pdf_links_in_page(html: str, base: str) -> list[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
    hrefs += re.findall(r'content=["\']([^"\']*\.pdf[^"\']*)["\']', html, re.I)
    links = []
    for h in hrefs:
        if re.search(r"\.pdf(\?|$)|/bitstream/|/bitstreams/|/download|/files/|/content/", h, re.I):
            url = urllib.parse.urljoin(base, h)
            if url not in links and not is_blocked(url):
                links.append(url)
    return links[:10]


def try_download(candidates: list[tuple[str, str]]) -> tuple[bytes | None, str | None]:
    for kind, url in candidates:
        try:
            data, final = fetch(url)
        except Exception:
            continue
        if is_pdf(data):
            return data, url
        if kind == "page":
            for link in pdf_links_in_page(data.decode("utf-8", "ignore"), final):
                try:
                    data2, _ = fetch(link)
                except Exception:
                    continue
                if is_pdf(data2):
                    return data2, link
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--email", required=True, help="contact email for OpenAlex / Unpaywall (their usage policy)")
    ap.add_argument("--download", metavar="DIR", help="staging folder for downloaded PDFs")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    socket.setdefaulttimeout(60)
    rows, fields = read_manifest(args.manifest)
    for col in ("oa", "oa_urls"):
        if col not in fields:
            fields.append(col)
    if args.download:
        os.makedirs(args.download, exist_ok=True)

    for row in rows:
        if row.get("status") == "downloaded" or row.get("lang") == "zh":
            continue  # CNKI papers have no Unpaywall coverage; download them in the browser
        label = f"{row.get('id', '?')} {row.get('first_author', '')} {row.get('year', '')}"
        if not row.get("doi"):
            fill_doi_from_title(row, args.email)
        doi = row.get("doi", "").strip()
        if not doi:
            print(f"NO-DOI   {label}")
            continue
        is_oa, candidates = oa_candidates(doi, args.email)
        row["oa"] = "true" if is_oa else "false"
        row["oa_urls"] = ";".join(u for _, u in candidates)
        if not args.download:
            print(f"{'OA ' if is_oa else 'PAY'}  {len(candidates):2d} candidates  {label}")
            continue
        data, used = try_download(candidates)
        if data:
            name = re.sub(r"[^\w.-]", "_", doi) + ".pdf"
            with open(os.path.join(args.download, name), "wb") as fh:
                fh.write(data)
            print(f"GOT      {len(data) / 1048576:5.2f}MB  {label}  <- {urllib.parse.urlparse(used).netloc}")
        else:
            print(f"{'OA-MISS' if is_oa else 'PAYWALL'}  {label}  (try browser + institution / document delivery)")
        time.sleep(0.3)

    write_manifest(args.manifest, rows, fields)
    print("\nmanifest updated:", args.manifest)


if __name__ == "__main__":
    main()
