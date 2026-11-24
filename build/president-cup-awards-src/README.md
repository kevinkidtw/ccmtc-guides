# president-cup-awards 原始檔

115 年總統盃 AI 素養爭霸賽（全國決賽暨頒獎典禮）屏南地區榮譽榜 → 官網「最新消息」公告（2026-11-24 發布，id `president-cup-ai-awards-2026-1124`）。

全國賽，公告版面比一般消息醒目：頂部深藍橫幅 + 每隊一張獎項卡片。
比照扶輪盃公告：只列屏南地區隊伍、不放學生與指導教師姓名、不附 PDF（原始 PDF 含其他縣市名單，不放進 repo）。

| 檔案 | 用途 |
|---|---|
| `data.json` | 屏南地區得獎隊伍（no 隊伍編號、g 組別、a 獎項、s 學校）與各組獲獎名額 |
| `make_announcement.py` | 由 data.json 產生 `announcement.html`（公告內文，contentFormat=html） |

## 改名單後重新產生

```bash
cd ccmtc-guides/build/president-cup-awards-src
python3 make_announcement.py
```

產生後到 `/admin-center` 編輯該則公告、貼上 announcement.html 的內容。內文以 `white-space: pre-wrap` 顯示，HTML 須維持單行。
