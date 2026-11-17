#!/usr/bin/env python3
"""ccmtc-guides 建置：依 build/manifests/<key>.json 把原始網頁與附件匯入 site/<key>/。

每份 manifest 描述一個說明站：
  source_root  原始資料夾（可用 ~ 開頭；也可用環境變數 GUIDES_SRC_<KEY> 覆寫）
  index        主頁 HTML（相對於 source_root），會複製成 site/<key>/index.html
  downloads    附件清單：from（來源）、to（site/<key>/downloads/ 底下的英數檔名）、
               name（使用者下載時看到的檔名）、label、note

另有 type: "mirror" 的封存站：archives/<key>/ 原樣複製到 site/<key>/。

匯入時會在主頁注入兩段（以註解標記，重跑會覆蓋，不會重複）：
  - 頁首上方的「← 競賽專區」返回列
  - 頁尾前的「檔案下載」區塊

用法：
  python3 build/build_site.py            # 建置全部 manifest
  python3 build/build_site.py drone      # 只建置指定站
"""
import html
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = ROOT / "build" / "manifests"
SITE = ROOT / "site"

BACK_START, BACK_END = "<!-- guides:backbar -->", "<!-- /guides:backbar -->"
DL_START, DL_END = "<!-- guides:downloads -->", "<!-- /guides:downloads -->"

BACKBAR = f"""{BACK_START}
<nav class="guides-backbar" style="max-width:1160px;margin:0 auto;padding:12px 16px 0;font-size:14px">
  <a href="/contests" style="color:inherit;opacity:.75;text-decoration:none">← 競賽專區</a>
  <span style="opacity:.4">｜</span>
  <a href="/" style="color:inherit;opacity:.75;text-decoration:none">車城自造教育科技中心</a>
</nav>
{BACK_END}"""


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} MB"


def downloads_section(items, out_dir: Path) -> str:
    rows = []
    for d in items:
        size = human_size((out_dir / "downloads" / d["to"]).stat().st_size)
        rows.append(
            "      <tr>"
            f"<td><a href=\"downloads/{html.escape(d['to'])}\" download=\"{html.escape(d['name'])}\">"
            f"{html.escape(d['label'])}</a></td>"
            f"<td>{html.escape(d.get('note', ''))}</td>"
            f"<td style=\"white-space:nowrap\">{size}</td></tr>"
        )
    return (
        f"{DL_START}\n"
        "  <section id=\"downloads\">\n"
        "    <h2>檔案下載</h2>\n"
        "    <table>\n"
        "      <tr><th>檔案</th><th>說明</th><th style=\"width:90px\">大小</th></tr>\n"
        + "\n".join(rows)
        + "\n    </table>\n  </section>\n"
        f"{DL_END}"
    )


def strip_block(text: str, start: str, end: str) -> str:
    while start in text and end in text:
        a = text.index(start)
        b = text.index(end, a) + len(end)
        text = text[:a] + text[b:]
    return text


def inject(page: str, backbar: str, downloads: str) -> str:
    page = strip_block(page, BACK_START, BACK_END)
    page = strip_block(page, DL_START, DL_END)

    i = page.find("<body")
    if i < 0:
        raise SystemExit("主頁找不到 <body>")
    j = page.index(">", i) + 1
    page = page[:j] + "\n" + backbar + page[j:]

    k = page.rfind("<footer")
    if k < 0:
        k = page.rfind("</body>")
    page = page[:k] + downloads + "\n\n  " + page[k:]
    return page


def build_mirror(m) -> None:
    """封存鏡像：archives/<key>/ 已是完整的靜態站，原樣複製到 site/<key>/。"""
    key = m["key"]
    src = ROOT / m["source"]
    if not (src / "index.html").is_file():
        raise SystemExit(f"[{key}] 封存來源缺少 index.html：{src}")
    out = SITE / key
    tmp = SITE / f".{key}.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(src, tmp)
    for p in tmp.rglob("*"):
        p.chmod(0o755 if p.is_dir() else 0o644)
    tmp.chmod(0o755)
    if out.exists():
        shutil.rmtree(out)
    tmp.rename(out)
    print(f"✅ [{key}] 封存鏡像 → site/{key}/")


def build(manifest_path: Path) -> None:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = m["key"]
    if m.get("type") == "mirror":
        build_mirror(m)
        return
    src_root = Path(os.path.expanduser(os.environ.get(f"GUIDES_SRC_{key.upper()}", m["source_root"])))
    if not src_root.is_dir():
        raise SystemExit(f"[{key}] 找不到原始資料夾：{src_root}")

    out = SITE / key
    tmp = SITE / f".{key}.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "downloads").mkdir(parents=True)

    for d in m.get("downloads", []):
        if "/" in d["to"] or not d["to"].isascii():
            raise SystemExit(f"[{key}] 下載檔 to 必須是英數檔名：{d['to']}")
        shutil.copyfile(src_root / d["from"], tmp / "downloads" / d["to"])

    page = (src_root / m["index"]).read_text(encoding="utf-8")
    page = inject(page, BACKBAR, downloads_section(m.get("downloads", []), tmp))
    (tmp / "index.html").write_text(page, encoding="utf-8")

    for p in tmp.rglob("*"):
        p.chmod(0o755 if p.is_dir() else 0o644)
    tmp.chmod(0o755)

    if out.exists():
        shutil.rmtree(out)
    tmp.rename(out)
    print(f"✅ [{key}] 已建置 → site/{key}/（附件 {len(m.get('downloads', []))} 個）")


def main(argv):
    wanted = set(argv[1:])
    manifests = sorted(MANIFESTS.glob("*.json"))
    if wanted:
        manifests = [p for p in manifests if p.stem in wanted]
        missing = wanted - {p.stem for p in manifests}
        if missing:
            raise SystemExit(f"找不到 manifest：{', '.join(sorted(missing))}")
    SITE.mkdir(exist_ok=True)
    for p in manifests:
        build(p)


if __name__ == "__main__":
    main(sys.argv)
