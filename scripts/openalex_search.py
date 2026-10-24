"""Search OpenAlex by keywords or forward citations, keeping only journals on a whitelist.

Two ways to collect candidates (combine freely, results are de-duplicated by DOI):
  --query "text"      keyword search over title + abstract (repeatable)
  --cites DOI         papers that cite this DOI, i.e. forward citation tracking (repeatable)

Every hit is kept only if its journal ISSN is in the whitelist CSV (columns: journal, issn, level),
e.g. assets/swufe_2025_business_management_A1plus.csv. Hits already in a manifest (by DOI) are
flagged so you only screen new ones.

Usage:
  python openalex_search.py --whitelist ../assets/swufe_2025_business_management_A1plus.csv \
      --cites 10.1177/00222429231152264 --query "influencer contract" \
      --manifest manifest.csv --email you@example.com --out candidates.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.openalex.org/works"
PER_PAGE = 200
MAX_PAGES = 5


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "literature-collection/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:  # network hiccups: retry, then report
            if attempt == 2:
                print(f"  request failed: {exc}", file=sys.stderr)
                return {}
            time.sleep(2 * (attempt + 1))
    return {}


def norm_doi(doi: str | None) -> str:
    return (doi or "").lower().replace("https://doi.org/", "").strip()


def load_whitelist(path: str) -> dict[str, tuple[str, str]]:
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out[row["issn"].strip().upper()] = (row["journal"].strip(), row["level"].strip())
    return out


def load_manifest_dois(path: str | None) -> set[str]:
    if not path:
        return set()
    with open(path, encoding="utf-8-sig") as f:
        return {norm_doi(r.get("doi")) for r in csv.DictReader(f) if r.get("doi")}


def abstract_text(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)


def work_id_for_doi(doi: str, email: str) -> str | None:
    data = get_json(f"{API}/doi:{urllib.parse.quote(norm_doi(doi))}?mailto={email}")
    wid = data.get("id", "")
    return wid.rsplit("/", 1)[-1] if wid else None


def fetch_all(filter_expr: str, search: str | None, email: str) -> list[dict]:
    # title_and_abstract.search avoids the full-text matches that make plain `search` noisy
    if search:
        filter_expr += f",title_and_abstract.search:{search.replace(',', ' ')}"
    # page-number paging: cursor paging beyond page 1 answers 401 without an API key
    works = []
    for page in range(1, MAX_PAGES + 1):
        params = {"filter": filter_expr, "per-page": PER_PAGE, "page": page, "mailto": email}
        data = get_json(f"{API}?{urllib.parse.urlencode(params)}")
        results = data.get("results", [])
        works += results
        if len(results) < PER_PAGE:
            break
    if search:
        # OpenAlex always stems ("influencer" also hits "influence"); keep only literal word-prefix matches
        tokens = [re.compile(r"\b" + re.escape(t), re.I) for t in search.split()]
        works = [w for w in works
                 if all(t.search(f"{w.get('title') or ''} {abstract_text(w.get('abstract_inverted_index'))}")
                        for t in tokens)]
    return works


def issn_filter(whitelist: dict) -> str:
    return "primary_location.source.issn:" + "|".join(sorted(whitelist))


def to_row(w: dict, whitelist: dict, via: str, known: set[str]) -> dict | None:
    src = (w.get("primary_location") or {}).get("source") or {}
    issns = [i.upper() for i in (src.get("issn") or [])]
    hit = next((whitelist[i] for i in issns if i in whitelist), None)
    if not hit or w.get("type") not in ("article", "review"):
        return None
    doi = norm_doi(w.get("doi"))
    return {
        "doi": doi, "title": w.get("title") or "", "year": w.get("publication_year") or "",
        "journal": hit[0], "level": hit[1], "cited_by": w.get("cited_by_count", 0), "via": via,
        "in_manifest": "yes" if doi in known else "",
        "abstract": abstract_text(w.get("abstract_inverted_index")),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--whitelist", required=True)
    ap.add_argument("--query", action="append", default=[])
    ap.add_argument("--cites", action="append", default=[])
    ap.add_argument("--from-year", type=int, default=2015)
    ap.add_argument("--manifest")
    ap.add_argument("--email", required=True, help="contact email for the OpenAlex polite pool")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    whitelist = load_whitelist(args.whitelist)
    known = load_manifest_dois(args.manifest)
    base = f"{issn_filter(whitelist)},from_publication_date:{args.from_year}-01-01"
    rows: dict[str, dict] = {}

    for doi in args.cites:
        wid = work_id_for_doi(doi, args.email)
        if not wid:
            print(f"cites {doi}: not found in OpenAlex", file=sys.stderr)
            continue
        works = fetch_all(f"cites:{wid},{base}", None, args.email)
        print(f"cites {doi}: {len(works)} whitelisted citing works")
        for w in works:
            r = to_row(w, whitelist, f"cites:{doi}", known)
            if r and r["doi"]:
                rows.setdefault(r["doi"], r)
    for q in args.query:
        works = fetch_all(base, q, args.email)
        print(f'query "{q}": {len(works)} whitelisted works')
        for w in works:
            r = to_row(w, whitelist, f"query:{q}", known)
            if r and r["doi"]:
                if r["doi"] in rows:
                    rows[r["doi"]]["via"] += f"; query:{q}"
                else:
                    rows[r["doi"]] = r

    fields = ["doi", "title", "year", "journal", "level", "cited_by", "via", "in_manifest", "abstract"]
    ordered = sorted(rows.values(), key=lambda r: (r["in_manifest"] == "yes", -int(r["cited_by"] or 0)))
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(ordered)
    new = sum(1 for r in ordered if not r["in_manifest"])
    print(f"wrote {len(ordered)} candidates ({new} not yet in manifest) -> {args.out}")


if __name__ == "__main__":
    main()
