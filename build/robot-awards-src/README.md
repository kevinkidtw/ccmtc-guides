# robot-awards 原始檔

2026 全國 AI 智創機器人競賽－扶輪盃 得獎名單 → 官網「最新消息」公告（2026-11-24 發布，綁定 `robot` 說明站）。
不另建榜單站，公告只列屏南地區隊伍（前三名表、佳作表），不列其他縣市、不附 PDF。

| 檔案 | 用途 |
|---|---|
| `rotary-cup-2026-awards.pdf` | 主辦單位公告版名單（選手、教師姓名已遮蔽），只作為 data.json 的來源，不放到網站 |
| `data.json` | 從 PDF 轉出的 65 筆得獎隊伍。e：energy 物資能源爭霸戰／target 標靶爭奪賽；g：es/jh 國小/國中 + r 偏鄉/g 一般；no 編號；t 隊名；c 縣市；a 獎項；s 學校 |
| `make_announcement.py` | 由 data.json 產生 `announcement.html`（公告內文，contentFormat=html） |

## 改名單後重新產生

```bash
cd ccmtc-guides/build/robot-awards-src
python3 make_announcement.py
```

產生後到 `/admin-center` 編輯該則公告、貼上 announcement.html 的內容即可。
公告內文以 `white-space: pre-wrap` 顯示，表格須維持單行，產生器已處理。
