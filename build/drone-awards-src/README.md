# drone-awards 原始檔

2026 屏東縣無人機競賽（115.11.20–21，南州國中）屏南地區得獎榮譽榜。

| 檔案 | 用途 |
|---|---|
| `data.json` | 得獎名單（79 筆）。e：soccer/ring/prog/sim；g：jh 國中 / es 國小；r：1 金 2 銀 3 銅 4 佳作；s 學校；t 隊名 |
| `template.html` | 榜單頁模板，`__DATA__` 會被替換成 data.json |
| `posters.py` + `poster_common.css` + `qr.svg` | 產生兩張海報的 HTML（out/p1.html、out/p2.html） |
| `shot.py` | 用 Playwright + Chrome 把 HTML 截成 PNG |

## 改名單後重新產生

```bash
cd ccmtc-guides/build/drone-awards-src
mkdir -p out
python3 -c "t=open('template.html').read();open('out/index.html','w').write(t.replace('__DATA__',open('data.json').read()))"
python3 posters.py
python3 shot.py file://$PWD/out/p1.html out/poster-highlights.png 1080 1350 0
python3 shot.py file://$PWD/out/p2.html out/poster-full.png 1240 1754 0
cp out/index.html out/poster-*.png ../../archives/drone-awards/
python3 ../build_site.py drone-awards && python3 ../verify_site.py --quick
```

（shot.py 預設 Chrome 路徑為 /usr/bin/google-chrome，Mac 上請改成 Chrome 的實際路徑或拿掉 executable_path。）

## 海報縮圖內嵌（選用）

模板裡的海報縮圖預設用相對路徑 `poster-*.png`，部署後就能正常顯示。目前線上版是把 640px 寬的 JPEG 縮圖用 base64 直接嵌進 index.html，
這樣即使單獨打開 index.html 預覽也看得到海報（需要 Pillow）：

```bash
python3 - <<'PY'
from PIL import Image; import base64, io
t = open('out/index.html', encoding='utf-8').read()
for n in ['poster-highlights', 'poster-full']:
    im = Image.open(f'out/{n}.png').convert('RGB'); im = im.resize((640, round(im.height*640/im.width)))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=82, optimize=True, progressive=True)
    t = t.replace(f'<img src="{n}.png"', '<img src="data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode() + '"')
open('out/index.html', 'w', encoding='utf-8').write(t)
PY
```
