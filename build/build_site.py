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
  <a href="#downloads" style="float:right;color:#1e5eff;font-weight:700;text-decoration:none">⬇ 檔案下載</a>
</nav>
{BACK_END}"""


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} MB"


# 下載卡片樣式：沿用說明站頁面既有的色票（--primary-soft、--accent-soft…），
# 頁面沒有定義時退回預設色，讓區塊單獨放進其他頁面也能用。
DL_CSS = """
<style>
#downloads .dl-lead{margin:-4px 0 12px;color:var(--muted,#5a6577);font-size:14px}
#downloads .dl-list{display:flex;flex-direction:column;gap:10px}
#downloads .dl-card{display:flex;align-items:center;gap:14px;border:1px solid var(--line,#d8e0ea);border-radius:10px;
  padding:12px 14px;background:var(--card,#fff)}
#downloads .dl-card.primary{border-left:4px solid var(--primary,#1e5eff)}
#downloads .dl-type{flex:0 0 auto;width:42px;height:42px;border-radius:8px;display:grid;place-items:center;
  font:700 12px/1 ui-monospace,"SF Mono",Menlo,monospace;background:#eef2f7;color:#334155}
#downloads .dl-body{flex:1;min-width:0}
#downloads .dl-title{font-weight:700;font-size:15px;line-height:1.4}
#downloads .dl-note{margin:2px 0 0;font-size:13.5px;color:var(--muted,#5a6577)}
#downloads .dl-meta{font-size:12.5px;color:var(--muted,#5a6577)}
#downloads .dl-actions{flex:0 0 auto;display:flex;gap:8px}
#downloads .dl-btn{padding:6px 12px;border-radius:7px;font-weight:700;font-size:13.5px;text-decoration:none;white-space:nowrap;
  border:1px solid var(--line,#d8e0ea);color:var(--ink,#1a2230);background:var(--card,#fff)}
#downloads .dl-btn:hover{border-color:var(--primary,#1e5eff);color:var(--primary,#1e5eff)}
#downloads .dl-btn.main{background:var(--primary,#1e5eff);border-color:var(--primary,#1e5eff);color:#fff}
@media (max-width:600px){
  #downloads .dl-card{flex-wrap:wrap}
  #downloads .dl-actions{width:100%;padding-left:56px}
}
</style>
"""

TYPE_LABEL = {".hex": "HEX", ".ts": "TS", ".pdf": "PDF", ".jpg": "JPG", ".jpeg": "JPG", ".png": "PNG", ".zip": "ZIP"}
VIEWABLE = {".pdf", ".jpg", ".jpeg", ".png"}


def downloads_section(items, out_dir: Path) -> str:
    rows = []
    for d in items:
        f = out_dir / "downloads" / d["to"]
        ext = f.suffix.lower()
        label = TYPE_LABEL.get(ext, ext.lstrip(".").upper()[:4] or "FILE")
        href = f"downloads/{html.escape(d['to'])}"
        name = html.escape(d["name"])
        primary = bool(d.get("primary"))
        actions = [f'<a class="dl-btn main" href="{href}" download="{name}">下載</a>']
        if ext in VIEWABLE:
            actions.append(f'<a class="dl-btn" href="{href}" target="_blank" rel="noopener">線上看</a>')
        rows.append(
            f'    <div class="dl-card{" primary" if primary else ""}">'
            f'<div class="dl-type">{label}</div>'
            f'<div class="dl-body"><div class="dl-title">{html.escape(d["label"])}</div>'
            f'<p class="dl-note">{html.escape(d.get("note", ""))}</p>'
            f'<div class="dl-meta">{name}・{human_size(f.stat().st_size)}</div></div>'
            f'<div class="dl-actions">{"".join(actions)}</div></div>'
        )
    return (
        f"{DL_START}\n" + DL_CSS +
        '  <section id="downloads">\n'
        "    <h2>檔案下載</h2>\n"
        '    <div class="dl-list">\n' + "\n".join(rows) + "\n    </div>\n  </section>\n"
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
