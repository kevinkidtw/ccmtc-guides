#!/usr/bin/env python3
"""把線上「2026 屏東縣屏南區 STEAM AI 智創機器人競賽」入口（Next.js，/competition）凍結成靜態封存。

做法（凍結鏡像）：原本的頁面與編譯後的 JS/CSS 原樣保留，只把頁面在瀏覽器端呼叫的三個
唯讀 API 換成靜態 JSON 檔，所以排行榜、分組賽程、報名名單都照原本的程式呈現，不必重寫。

  archives/competition/
    index.html, rules/, leaderboard/, teams/   線上頁面的 HTML（只多一行 archive.css 連結）
    archive.css                                 封存橫幅、隱藏寫入按鈕
    admin/, referee/                            改成「已封存」說明頁（後台與計分已停用）
    scoring/                                    舊網址，轉到成績大廳
    api/leaderboard, api/competitions, api/announcements   凍結的 JSON（選手姓名已遮蔽）
    _next/static/…, *.jpg, favicon.ico          編譯後資源與圖片（原樣）

只在封存當天執行一次（之後原系統就下線了）：
  python3 build/capture_competition.py <raw 目錄>

<raw 目錄> 需包含：
  .next/static/、public/      從 ccmtc-competition 容器匯出（docker exec … tar）
  page-index.html、page-rules.html、page-leaderboard.html、page-teams.html
  leaderboard.json、competitions.json、announcements.json   線上 API 的回應
  favicon.ico
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "archives" / "competition"
PREFIX = "/competition"

TITLE = "2026 屏東縣屏南區國中小 STEAM AI 智創機器人競賽"

# 純 CSS（獨立的 archive.css，不快取）。
ARCHIVE_CSS_RULES = """body::before{content:"📦 本賽事已於 2026 年 6 月結束，此頁為封存資料（唯讀）。成績與名單以封存當時為準。";
  display:block;padding:10px 16px;background:#334155;color:#f8fafc;font:600 14px/1.6 system-ui,"Noto Sans TC",sans-serif;
  text-align:center;letter-spacing:.02em}
/* 封存後不提供任何寫入操作 */
.draw-btn,.reset-draw-btn{display:none!important}
a[href$="/competition/referee"],a[href$="/competition/admin"]{display:none!important}
"""

NOTICE_PAGE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} · 已封存</title>
<style>
:root{{--bg:#f4f6f8;--card:#fff;--ink:#0f172a;--muted:#475569;--line:#cbd5e1;--link:#1d4ed8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b0f17;--card:#131b26;--ink:#f1f5f9;--muted:#94a3b8;--line:#334155;--link:#60a5fa}}}}
body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:16px;background:var(--bg);color:var(--ink);
  font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif}}
.card{{max-width:460px;background:var(--card);border:1px solid var(--line);border-top:4px solid #64748b;border-radius:4px;padding:28px}}
h1{{font-size:22px;margin:0 0 10px}} p{{line-height:1.75;color:var(--muted);margin:0 0 14px}} a{{color:var(--link)}}
</style></head>
<body><div class="card">
<h1>{heading}已停用</h1>
<p>{title}已於 2026 年 6 月結束，系統改為封存資料，{heading}不再提供。</p>
<p><a href="{prefix}/">查看賽事封存首頁</a>　<a href="{prefix}/leaderboard">成績大廳</a>　<a href="/contests">競賽專區</a></p>
</div></body></html>
"""

REDIRECT_PAGE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}"><title>成績大廳</title></head>
<body><p><a href="{target}">前往成績大廳</a></p></body></html>
"""


def mask_name(name):
    """和原系統 teams 頁的遮蔽規則一致；對已遮蔽的字串再套一次結果不變。"""
    if not isinstance(name, str):
        return name
    chars = list(name.strip())
    if not chars:
        return name
    if len(chars) == 1:
        return "Ｏ"
    if len(chars) == 2:
        return chars[0] + "Ｏ"
    return chars[0] + "Ｏ" + chars[-1]


NAME_KEYS = {"s1", "s2", "s3", "s4", "student1", "student2", "studentName", "coach", "coachName",
             "teacher", "teacherName", "contactName", "phone", "email", "contactPhone", "contactEmail"}
DROP_KEYS = {"phone", "email", "contactPhone", "contactEmail"}


def scrub(x):
    if isinstance(x, list):
        return [scrub(v) for v in x]
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if k in DROP_KEYS:
                continue
            out[k] = mask_name(v) if k in NAME_KEYS and isinstance(v, str) else scrub(v)
        return out
    return x


def patch_html(html: str) -> str:
    """只在 </head> 前加一個樣式表連結，其餘一字不改。
    不能改 <title> 或刪原有標籤：Next/React 會比對，內容不同就 hydration 失敗（React #418）；
    React 19 會略過 <head> 裡多出來的標籤，所以「只加」是安全的。
    不把封存樣式附加到原本的 CSS 檔：那個檔名當初以一年 immutable 快取送出，
    來過的訪客瀏覽器只會用舊檔，看不到封存橫幅。"""
    link = f'<link rel="stylesheet" href="{PREFIX}/archive.css">'
    assert "</head>" in html
    return html.replace("</head>", link + "</head>", 1)


# 原系統把後台／裁判密碼寫死在前端程式裡（會送到每位訪客的瀏覽器）。
# 封存時換成同長度的無效字串；後台已停用、API 一律 403，換掉不影響畫面。
# 要移除的字串由環境變數 ARCHIVE_SCRUB 傳入（逗號分隔），不寫進原始碼：
#   ARCHIVE_SCRUB="$OLD_PASS" python3 build/capture_competition.py <raw>
LEAKED_STRINGS = {
    k: ("_" * len(k))
    for k in (x.strip() for x in __import__("os").environ.get("ARCHIVE_SCRUB", "").split(","))
    if k
}


def scrub_static(static_dir: Path) -> None:
    for f in static_dir.rglob("*.js"):
        s = f.read_text(encoding="utf-8")
        t = s
        for k, v in LEAKED_STRINGS.items():
            t = t.replace(k, v)
        if t != s:
            f.write_text(t, encoding="utf-8")


def write_archive_css(out: Path) -> None:
    (out / "archive.css").write_text("/* 封存樣式（capture_competition.py 產生） */\n" + ARCHIVE_CSS_RULES, encoding="utf-8")


def main(raw: Path):
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    pages = {"index": "", "rules": "rules", "leaderboard": "leaderboard", "teams": "teams"}
    for name, sub in pages.items():
        src = (raw / f"page-{name}.html").read_text(encoding="utf-8")
        dest = OUT / sub / "index.html" if sub else OUT / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(patch_html(src), encoding="utf-8")

    for sub, heading in (("admin", "後台管理"), ("referee", "裁判計分")):
        d = OUT / sub
        d.mkdir()
        (d / "index.html").write_text(NOTICE_PAGE.format(title=TITLE, heading=heading, prefix=PREFIX), encoding="utf-8")
    (OUT / "scoring").mkdir()
    (OUT / "scoring" / "index.html").write_text(REDIRECT_PAGE.format(target=f"{PREFIX}/leaderboard"), encoding="utf-8")

    api = OUT / "api"
    api.mkdir()
    for name in ("leaderboard", "competitions", "announcements"):
        data = json.loads((raw / f"{name}.json").read_text(encoding="utf-8"))
        (api / name).write_text(json.dumps(scrub(data), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    shutil.copytree(raw / ".next" / "static", OUT / "_next" / "static")
    scrub_static(OUT / "_next" / "static")
    write_archive_css(OUT)
    for f in (raw / "public").iterdir():
        if f.is_file() and not f.name.startswith("."):
            shutil.copy2(f, OUT / f.name)
    shutil.copy2(raw / "favicon.ico", OUT / "favicon.ico")

    for p in OUT.rglob("*"):
        p.chmod(0o755 if p.is_dir() else 0o644)
    print(f"✅ 封存鏡像完成 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
