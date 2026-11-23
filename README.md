# ccmtc-guides — 官網共用靜態說明站容器

車城自造教育科技中心官網（`https://ccmtc.mooo.com`）底下所有**競賽說明站**共用的一個 nginx 靜態容器。
每個說明站是 `site/<key>/` 一個資料夾，由 `ccmtc-portal` 依站台清單把 `/<key>/…` rewrite 進來。

> 為什麼不再一站一個容器：說明站越來越多（機器人、機關王、無人機…），
> 每站一個容器＋一組登入頁＋一條 rewrite＋一個導覽連結，維護成本線性成長。
> 改成「一個容器 + 一份清單」後，上新站只要兩步。

| 站 | 路徑 | 通行碼 | 來源 |
|---|---|---|---|
| 屏東縣無人機競賽 公版程式說明站 | `/drone/` | 公開 | `build/manifests/drone.json` |
| 2026 屏南區 STEAM AI 智創機器人競賽（封存） | `/competition/` | 公開、唯讀 | `build/manifests/competition.json`（type: mirror） |
| 2026 屏東縣無人機競賽 屏南地區得獎榮譽榜 | `/drone-awards/` | 公開 | `build/manifests/drone-awards.json`（type: mirror，原始資料在 `build/drone-awards-src/`） |
| 智創機器人程式說明站 | `/robot/` | 公開 | `../robot-guide/site`（type: mirror） |
| 機關王 R4M 程式說明站 | `/r4m/` | 公開 | `../r4m-guide/site`（type: mirror） |
| 魷來魷去 AI 教材站 | `/squid/` | 公開 | `../squid-portal/site`（type: mirror） |

## 架構

```
瀏覽器 ─HTTPS→ DSM 反向代理 → ccmtc-portal (Next.js, 3040)
                                 ├─ src/config/sites.mjs   ← 站台清單（唯一設定來源）
                                 ├─ src/middleware.js      ← 結尾斜線導正、通行碼驗證
                                 └─ rewrite /<key>/… ─→ guides 容器 (nginx:alpine, 內網 80)
                                                          └─ /volume1/docker/ccmtc-guides/site/<key>/
```

- 容器只 `expose: 80`，不對外開埠，一律經 portal 進來。
- 目前所有說明站公開。若某站日後需要通行碼，一律在 portal 伺服器端驗證（`sites.mjs` 的 `auth`），靜態檔內不放任何密碼檢查。
- 根目錄 `/` 回 404，隱藏檔回 404；`.hex`、`.ts` 等程式檔強制以附件下載。

## 新增一個說明站

1. **準備原始檔**：主頁 HTML（建議單檔、不引用外部 CDN）與要提供下載的附件。
2. **寫 manifest**：複製 `build/manifests/drone.json` 改成 `<key>.json`。
   `key` 為小寫英數（例：`drone`），附件的 `to` 用英數檔名、`name` 是使用者下載時看到的中文檔名。
3. **建置與驗證**：
   ```bash
   python3 build/build_site.py <key>
   python3 build/verify_site.py --quick
   ```
4. **登記到官網清單**：在 `ccmtc-official/ccmtc-portal/src/config/sites.mjs` 加一筆，`upstream: 'guides'`。
   需要通行碼的話填 `auth: { envVar, cookie, signMessage }`，並請管理者在 NAS 的
   `/volume1/docker/ccmtc-official/.env` 加上該環境變數（通行碼不經過對話或腳本）。
5. **部署**：先部署 portal（rewrite 在建置時產生），再執行本專案的 `./deploy_nas.sh`。

## 賽事結束：封存

把 `sites.mjs` 裡該站的 `status` 改成 `'archived'`（必要時把 `featured` 改 `false`）。
網址照常可開，首頁卡片撤下，競賽專區移到「已封存」並標示。不要刪資料夾，避免公文、簡章上的連結失效。

## 建置腳本

| 檔案 | 用途 |
|---|---|
| `build/build_site.py` | 依 manifest 從原始資料夾匯入主頁與附件到 `site/<key>/`，並注入「← 競賽專區」返回列與「檔案下載」區塊（以 HTML 註解標記，可重跑） |
| `build/verify_site.py --quick` | 靜態檢查：index 存在、相對連結有效、無外部 script/stylesheet、無隱藏檔 |
| `build/verify_site.py --url https://ccmtc.mooo.com` | 線上回歸：`/<key>` → 308、首頁與附件 200（或需通行碼站 302），程式檔需為附件 |

原始資料夾路徑寫在 manifest 的 `source_root`，也可用環境變數 `GUIDES_SRC_<KEY>` 臨時覆寫。

## 本機測試

```bash
docker compose up -d     # http://localhost:3100/drone/
```

或不用 Docker：`python3 -m http.server 3100 --directory site`，再以 `npm run dev` 啟動 portal（開發模式預設指向 `127.0.0.1:3100`）。

## 首次部署（NAS）

在 `/volume1/docker/ccmtc-official/docker-compose.yml` 加入：

```yaml
  # 官網共用靜態說明站（對應 NAS 的 ../ccmtc-guides，純靜態 nginx）
  guides:
    image: nginx:alpine
    container_name: ccmtc-guides
    restart: unless-stopped
    expose:
      - "80"
    volumes:
      - ../ccmtc-guides/site:/usr/share/nginx/html:ro
      - ../ccmtc-guides/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

之後執行 `./deploy_nas.sh`；它會先確認 compose 已有 `guides` 服務，再同步、重啟並做線上驗證。

## 舊獨立容器併入（2026-11-23 完成）

`/robot`、`/r4m`、`/squid` 原本各自一個 nginx 容器（`robot-guide`、`r4m-guide`、`squid-portal`），
已併入本容器，NAS 上的舊容器已移除、compose 也拿掉對應服務。網址、cookie 都不變。

- 內容仍在各自專案維護：改完先在 `../robot-guide` 等專案建置出 `site/`，再執行本專案 `./deploy_nas.sh`。
  各專案自己的 `deploy_nas.sh` 已不再使用。
- manifest 是 `type: mirror`、`source` 指向 `../<專案>/site`，建置時原樣複製，不注入返回列。
- `site/robot`、`site/r4m`、`site/squid` 是建置產物，不進版控（squid 含主辦單位教材，原 repo 為私人）。
- `.pptx` 以附件下載（沿用 squid 舊容器行為），已加進 `nginx.conf`。

## 封存鏡像（type: mirror）

已結束、原本是動態系統的賽事網站，用「凍結鏡像」封存：原頁面與編譯後的 JS/CSS 原樣保留，
頁面在瀏覽器端呼叫的唯讀 API 換成靜態 JSON（`archives/<key>/api/…`），原程式照常顯示排行榜、名單，
但沒有任何後端，寫入一律 403。

第一個是 `/competition/`（2026 屏南區智創機器人競賽，2026-11-18 封存），由 `build/capture_competition.py` 產生：

- 頁面 HTML **只多一行** `archive.css` 連結，其餘一字不改。改 `<title>` 或刪標籤會讓 React hydration 失敗（#418）。
- 封存橫幅與隱藏「抽籤／重置／裁判／後台」都寫在獨立的 `archive.css`。不能附加到原本的 CSS 檔：那個檔名當初以一年 immutable 快取送出，來過的訪客看不到更新。
- 凍結的 JSON 中選手姓名已依原系統規則遮蔽（陳Ｏ豪），聯絡資料欄位一律移除。
- 原系統程式與資料庫保留在 NAS 的 `/volume1/docker/ccmtc-competition`，備份在 `ccmtc-backups-safety/ccmtc-competition-archive-20261118-0053.tgz`（本機 `_備份/` 也有一份）。

本機測試請用 `python3 build/serve_local.py`（行為對齊 nginx）；`python3 -m http.server` 會對資料夾回 301，結果不準。
透過 portal 的 `next dev` 代理看封存頁會出現 React #418，這是開發模式代理造成的，正式環境沒有。
