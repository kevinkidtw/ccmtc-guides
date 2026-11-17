#!/usr/bin/env python3
"""本機測試用靜態伺服器，行為對齊正式 nginx.conf：
  - $uri → $uri/index.html，不對資料夾回 301 補斜線（官網 rewrite 會吃掉結尾斜線）
  - /<站>/api/* 視為 JSON，只允許 GET/HEAD
用法：python3 build/serve_local.py [port]   （預設 3100，服務 site/）
"""
import http.server
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(SITE), **k)

    def send_head(self):
        path = self.translate_path(self.path)
        p = Path(path)
        if p.is_dir():
            idx = p / "index.html"
            if not idx.is_file():
                self.send_error(404)
                return None
            self.path = self.path.split("?")[0].rstrip("/") + "/index.html"
        return super().send_head()

    def guess_type(self, path):
        if "/api/" in str(path).replace("\\", "/"):
            return "application/json"
        return super().guess_type(path)

    def do_POST(self):
        self.send_error(403)

    do_PUT = do_DELETE = do_PATCH = do_POST


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3100
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
