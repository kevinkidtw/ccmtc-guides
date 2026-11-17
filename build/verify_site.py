#!/usr/bin/env python3
"""ccmtc-guides 驗證。

  --quick         靜態檢查 site/ 底下每個站：
                    - 有 index.html，且有 manifest 對應
                    - 頁內相對連結（href/src）都指到存在的檔案
                    - 不載入外部 script／stylesheet（賽場可能沒網路，也避免第三方追蹤）
                    - 沒有隱藏檔或暫存資料夾殘留
  --url BASE      線上回歸：對 BASE（例如 https://ccmtc.mooo.com）逐站檢查
                    /<key> → 308、/<key>/ 與每個附件 → 200（公開站）或 302/307 導向登入（需通行碼站）
                  需要通行碼的站名單從 --locked 傳入（逗號分隔），預設全部視為公開。
"""
import argparse
import json
import re
import sys
import subprocess
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
MANIFESTS = ROOT / "build" / "manifests"

ATTR_RE = re.compile(r'\b(?:href|src)\s*=\s*"([^"]+)"', re.I)
EXT_SCRIPT_RE = re.compile(r'<script[^>]+src\s*=\s*"(?:https?:)?//', re.I)
EXT_CSS_RE = re.compile(r'<link[^>]+href\s*=\s*"(?:https?:)?//[^"]+"[^>]*stylesheet|<link[^>]+stylesheet[^>]+href\s*=\s*"(?:https?:)?//', re.I)


def quick() -> int:
    errors = []
    sites = sorted(p for p in SITE.iterdir() if p.is_dir()) if SITE.exists() else []
    if not sites:
        errors.append("site/ 底下沒有任何站")
    manifests = {p.stem for p in MANIFESTS.glob("*.json")}
    for d in sites:
        key = d.name
        if key.startswith("."):
            errors.append(f"殘留暫存資料夾：site/{key}")
            continue
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", key):
            errors.append(f"[{key}] 資料夾名稱須為小寫英數（同 sites.mjs 的 key）")
        if key not in manifests:
            errors.append(f"[{key}] 沒有對應的 build/manifests/{key}.json")
        for hidden in d.rglob(".*"):
            errors.append(f"[{key}] 隱藏檔不應部署：{hidden.relative_to(SITE)}")
        mirror = False
        if key in manifests:
            mirror = json.loads((MANIFESTS / f"{key}.json").read_text(encoding="utf-8")).get("type") == "mirror"
        index = d / "index.html"
        if not index.is_file():
            errors.append(f"[{key}] 缺少 index.html")
            continue
        for page in d.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            rel = page.relative_to(SITE)
            if mirror:
                # 封存鏡像的 HTML 必須和原系統一字不差（改了會 hydration 失敗），
                # 只檢查不含外部 script；原有的 Google Fonts 樣式表允許保留。
                if EXT_SCRIPT_RE.search(text):
                    errors.append(f"[{key}] {rel} 載入外部 script")
                continue
            if EXT_SCRIPT_RE.search(text):
                errors.append(f"[{key}] {rel} 載入外部 script")
            if EXT_CSS_RE.search(text):
                errors.append(f"[{key}] {rel} 載入外部 stylesheet")
            for url in ATTR_RE.findall(text):
                if re.match(r"^(?:[a-z]+:|//|#|/)", url, re.I):
                    continue  # 外部連結、錨點、站外絕對路徑（/contests 等官網頁）不檢查
                target = (page.parent / urllib.parse.unquote(url.split("#")[0].split("?")[0])).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    errors.append(f"[{key}] {rel} 連結不存在：{url}")
    for e in errors:
        print("❌", e)
    if not errors:
        print(f"✅ 靜態驗證通過（{len(sites)} 個站）")
    return 1 if errors else 0


def status(url: str):
    """用 curl 取狀態碼與標頭（不跟隨轉址）。不用 urllib：python.org 版 Python 常缺 CA 憑證。"""
    out = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-D", "-", "--max-time", "20",
         "-A", "ccmtc-guides-verify", url],
        capture_output=True, text=True,
    )
    lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    code = 0
    headers = {}
    for l in lines:
        if l.upper().startswith("HTTP/"):
            parts = l.split()
            code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            headers = {}
        elif ":" in l:
            k, v = l.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return code, headers


def live(base: str, locked: set) -> int:
    bad = 0
    base = base.rstrip("/")
    for mpath in sorted(MANIFESTS.glob("*.json")):
        m = json.loads(mpath.read_text(encoding="utf-8"))
        key = m["key"]
        ok_codes = {302, 307} if key in locked else {200}
        checks = [(f"/{key}", {308})]
        checks += [(f"/{key}/", ok_codes)]
        checks += [(f"/{key}/downloads/{d['to']}", ok_codes) for d in m.get("downloads", [])]
        for path, want in checks:
            code, headers = status(base + urllib.parse.quote(path))
            mark = "✅" if code in want else "❌"
            bad += code not in want
            print(f"{mark} {code} {path}  (預期 {sorted(want)})")
            if key not in locked and path.endswith((".hex", ".ts")) and code == 200:
                cd = headers.get("content-disposition", "")
                if "attachment" not in cd:
                    print(f"❌     {path} 缺少 Content-Disposition: attachment")
                    bad += 1
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--url")
    ap.add_argument("--locked", default="")
    a = ap.parse_args()
    if not a.quick and not a.url:
        a.quick = True
    rc = 0
    if a.quick:
        rc |= quick()
    if a.url:
        rc |= live(a.url, {k for k in a.locked.split(",") if k})
    sys.exit(rc)


if __name__ == "__main__":
    main()
