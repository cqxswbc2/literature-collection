"""Write <dest>/下载情况.md from manifest.csv plus what is actually on disk.

Sections: overview (counts + sizes measured on disk), folder tree, English papers by folder,
Chinese papers (journal / thesis), acquisition routes, still-missing papers with notes,
and a citation reminder when repository (accepted-manuscript) copies were used.

Usage:
  python make_summary.py manifest.csv --dest "已下载论文"
  python make_summary.py manifest.csv --dest "已下载论文" --topic "居民需求响应"
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys
from collections import Counter, defaultdict

ROUTE_LABELS = {
    "oa-direct": "出版社 OA 直链",
    "repository": "机构仓储镜像（可能为接受稿）",
    "browser-auto": "浏览器自动下载",
    "browser-manual": "用户在浏览器手动下载（OA）",
    "institution": "学校机构权限（用户手动下载）",
    "cnki": "CNKI（学校 IP）",
    "delivery": "图书馆文献传递",
    "": "未记录",
}


def read_manifest(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def disk_inventory(dest: str) -> dict[str, list[tuple[str, int]]]:
    """Map relative folder -> [(file name, size bytes)] for every PDF under dest."""
    inv: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for root, _, files in os.walk(dest):
        for name in files:
            if name.lower().endswith(".pdf"):
                rel = os.path.relpath(root, dest).replace(os.sep, "/")
                inv[rel].append((name, os.path.getsize(os.path.join(root, name))))
    return inv


def mb(n: int) -> str:
    return f"约 {n / 1048576:.0f} MB"


def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def paper_cells(r: dict, extra: str) -> list[str]:
    title = r.get("short_title", "")
    if r.get("priority"):
        title = f"{r['priority']} {title}"
    return [r.get("year", ""), r.get("first_author", ""), title, extra]


def build(rows: list[dict], inv: dict[str, list[tuple[str, int]]], topic: str) -> str:
    done = [r for r in rows if r.get("status") == "downloaded"]
    missing = [r for r in rows if r.get("status") != "downloaded"]
    lang_files = {k: [f for folder, fs in inv.items() if folder.startswith(k) for f in fs] for k in ("英文", "中文")}
    total_files = sum(len(v) for v in lang_files.values())
    total_size = sum(s for v in lang_files.values() for _, s in v)

    md = [f"# 下载情况总结（截至 {dt.date.today():%Y-%m-%d}）", ""]
    if topic:
        md += [f"主题：{topic}", ""]
    md += ["## 一、总览", ""]
    md += table(["", "篇数", "大小"], [
        ["英文全文", str(len(lang_files["英文"])), mb(sum(s for _, s in lang_files["英文"]))],
        ["中文全文", str(len(lang_files["中文"])), mb(sum(s for _, s in lang_files["中文"]))],
        ["**合计**", f"**{total_files}**", f"**{mb(total_size)}**"],
    ])
    untracked = total_files - len(done)
    md += ["", f"清单（manifest）里标记为已下载的有 {len(done)} 篇。"
           + (f"磁盘上另有 {untracked} 个 PDF 不在清单里，请核对。" if untracked > 0 else ""), ""]

    md += ["## 二、目录结构", "", "```"]
    md += [f"{folder}/  {len(files)} 篇" for folder, files in sorted(inv.items()) if folder != "."]
    md += ["```", ""]

    en = [r for r in done if r.get("lang") != "zh"]
    md += [f"## 三、英文 {len(en)} 篇", ""]
    by_folder: dict[str, list[dict]] = defaultdict(list)
    for r in en:
        by_folder[r.get("folder") or r.get("source") or "Other"].append(r)
    for folder in sorted(by_folder):
        group = sorted(by_folder[folder], key=lambda r: r.get("year", ""))
        md += [f"### {folder}（{len(group)}）", ""]
        md += table(["年", "作者", "题目", "获取途径"],
                    [paper_cells(r, ROUTE_LABELS.get(r.get("route", ""), r.get("route", ""))) for r in group])
        md.append("")

    zh = [r for r in done if r.get("lang") == "zh"]
    md += [f"## 四、中文 {len(zh)} 篇", ""]
    for label, kinds in (("期刊论文", ("journal", "")), ("学位论文", ("master", "phd"))):
        group = sorted([r for r in zh if r.get("kind", "") in kinds], key=lambda r: r.get("year", ""))
        if group:
            md += [f"### {label}（{len(group)}）", ""]
            md += table(["年", "作者", "题目", "来源"], [paper_cells(r, r.get("source", "")) for r in group])
            md.append("")

    md += ["## 五、获取途径统计", ""]
    counts = Counter((r.get("route", ""), "中文" if r.get("lang") == "zh" else "英文") for r in done)
    routes = sorted({route for route, _ in counts})
    md += table(["途径", "英文", "中文"],
                [[ROUTE_LABELS.get(rt, rt), str(counts[(rt, "英文")] or "—"), str(counts[(rt, "中文")] or "—")]
                 for rt in routes])
    md.append("")
    if any(r.get("route") == "repository" for r in done):
        md += ["**引用提醒**：机构仓储来的版本可能是作者接受稿，引用时按 DOI 对应的正式出处标注，"
               "不要用 PDF 上的页码。", ""]

    md += [f"## 六、还没下载的（{len(missing)} 篇）", ""]
    if missing:
        md += table(["优先级", "作者 / 年", "题目", "出处", "DOI", "备注"],
                    [[r.get("priority", ""), f"{r.get('first_author', '')} {r.get('year', '')}",
                      r.get("short_title", ""), r.get("source", ""), r.get("doi", ""), r.get("note", "")]
                     for r in missing])
        md += ["", "补救办法：学校机构权限 → 图书馆文献传递 / 馆际互借（CALIS、NSTL）→ 给通讯作者发邮件 → "
               "找 NBER / SSRN / 作者主页上的工作论文版。", ""]
    else:
        md += ["清单里的文献都已下载。", ""]
    return "\n".join(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--dest", required=True, help="archive root, e.g. 已下载论文")
    ap.add_argument("--topic", default="", help="topic line shown under the title")
    ap.add_argument("--out", help="output path (default: <dest>/下载情况.md)")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    out = args.out or os.path.join(args.dest, "下载情况.md")
    text = build(read_manifest(args.manifest), disk_inventory(args.dest), args.topic)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("written:", out)


if __name__ == "__main__":
    main()
