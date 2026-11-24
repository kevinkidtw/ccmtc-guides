"""由 data.json 產生最新消息公告用的 HTML（announcement.html）。

全國賽，版面比照總統盃公告加強：頂部橫幅 + 前三名大卡片 + 佳作小卡片。
只列屏南地區（屏東縣）隊伍，其他縣市不列；名單不放選手與指導教師姓名；公告不附 PDF。
公告內文以 white-space: pre-wrap 顯示，所以每個區塊的 HTML 都寫在同一行，區塊之間才用換行。
"""
import json, re
from collections import Counter

EVENT = {'energy': '物資能源爭霸戰', 'target': '標靶爭奪賽'}
GROUP = {'es-r': '國小偏鄉組', 'es-g': '國小一般組', 'jh-r': '國中偏鄉組', 'jh-g': '國中一般組'}
HOME = '屏東縣'  # 本屆屏東縣得獎隊伍皆為恆春半島（屏南地區）學校

# 獎項：圖示、色帶漸層、色帶文字色、組內名次（每組特優／優等／甲等各 1 隊，由 main() 檢查）
STYLE = {
    '特優': ('🥇', 'linear-gradient(135deg,#fde68a,#f59e0b)', '#78350f', 1),
    '優等': ('🥈', 'linear-gradient(135deg,#f1f5f9,#94a3b8)', '#1e293b', 2),
    '甲等': ('🥉', 'linear-gradient(135deg,#fed7aa,#c2410c)', '#431407', 3),
}


def short(s):
    s = re.sub(r'^(屏東縣|高雄市|臺東縣|臺南市)立?', '', s)
    s = re.sub(r'^\S{1,3}?[鄉鎮區市](?=\S{3,})', '', s)
    return s.replace('國民中學', '國中').replace('國民小學', '國小')


def top_card(r):
    icon, bg, fg, rank = STYLE[r['a']]
    return (
        '<div style="flex:1 1 220px;min-width:0;border-radius:16px;overflow:hidden;'
        'box-shadow:0 6px 18px rgba(15,23,42,.12);background:#fff;border:1px solid #e2e8f0">'
        f'<div style="background:{bg};color:{fg};padding:16px;text-align:center">'
        f'<div style="font-size:40px;line-height:1">{icon}</div>'
        f'<div style="font-size:24px;font-weight:900;letter-spacing:.15em;margin-top:6px">{r["a"]}</div>'
        f'<div style="font-size:13px;opacity:.85;margin-top:2px">該組全國第 {rank} 名</div></div>'
        '<div style="padding:14px 16px;text-align:center">'
        f'<div style="font-size:21px;font-weight:900;color:#0f172a">{r["t"]}</div>'
        f'<div style="font-size:16px;font-weight:700;color:#334155;margin-top:2px">{short(r["s"])}</div>'
        f'<div style="font-size:14px;color:#475569;margin-top:6px">{EVENT[r["e"]]}・{GROUP[r["g"]]}</div>'
        '</div></div>')


def merit_card(r):
    return (
        '<div style="flex:1 1 130px;min-width:0;border-radius:12px;background:#f0fdf4;'
        'border:1px solid #bbf7d0;padding:10px 12px">'
        f'<div style="font-size:16px;font-weight:800;color:#14532d">🏅 {r["t"]}</div>'
        f'<div style="font-size:14px;font-weight:700;color:#334155;margin-top:2px">{short(r["s"])}</div>'
        f'<div style="font-size:13px;color:#475569;margin-top:2px">{EVENT[r["e"]]}・{GROUP[r["g"]]}</div>'
        '</div>')


def heading(text):
    return f'<div style="font-size:18px;font-weight:900;color:#0f172a;margin:4px 0 8px">{text}</div>'


def main():
    data = json.load(open('data.json', encoding='utf-8'))
    per_group = Counter((r['e'], r['g'], r['a']) for r in data if r['a'] in STYLE)
    assert max(per_group.values()) == 1, '每組特優／優等／甲等應各 1 隊，否則「全國第 N 名」不成立'

    home = [r for r in data if r['c'] == HOME]
    top = sorted((r for r in home if r['a'] in STYLE), key=lambda r: STYLE[r['a']][3])
    merits = [r for r in home if r['a'] == '佳作']
    cnt = Counter(r['a'] for r in home)
    schools = len({short(r['s']) for r in home})

    banner = (
        '<div style="border-radius:18px;padding:22px 20px;color:#fff;text-align:center;'
        'background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#b45309 140%);margin:4px 0 14px">'
        '<div style="font-size:13px;letter-spacing:.25em;color:#fcd34d;font-weight:700">全國賽 · 屏南之光</div>'
        '<div style="font-size:26px;font-weight:900;margin:8px 0 6px;line-height:1.35">2026 全國 AI 智創機器人競賽－扶輪盃</div>'
        f'<div style="font-size:18px;font-weight:700">屏南 {schools} 校共獲 '
        f'<span style="color:#fcd34d;font-size:30px">{len(home)}</span> 項次</div>'
        f'<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:12px;font-size:14px;font-weight:700">'
        + ''.join(
            f'<span style="background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:4px 12px">{icon} {a} {cnt[a]}</span>'
            for a, (icon, *_rest) in STYLE.items())
        + f'<span style="background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:4px 12px">🏅 佳作 {cnt["佳作"]}</span>'
        '</div></div>')

    champions = '、'.join(f'{short(r["s"])}「{r["t"]}」' for r in top if r['a'] == '特優')
    intro = (
        f'賀！「2026 全國 AI 智創機器人競賽－扶輪盃」成績揭曉，屏南地區選手在物資能源爭霸戰、標靶爭奪賽兩項賽事表現亮眼，'
        f'共奪下 <b>{len(top)} 個前三名</b>，其中{champions}拿下<b>特優（組別第一名）</b>！')

    out = [
        banner,
        intro,
        '',
        heading('🏆 前三名'),
        '<div style="display:flex;flex-wrap:wrap;gap:14px;margin-bottom:4px">' + ''.join(top_card(r) for r in top) + '</div>',
        '',
        heading(f'🏅 佳作（{len(merits)} 隊）'),
        '<div style="display:flex;flex-wrap:wrap;gap:10px">' + ''.join(merit_card(r) for r in merits) + '</div>',
        '',
        '<span style="color:#475569;font-size:15px">恭喜獲獎的同學與指導老師！</span>',
    ]
    open('announcement.html', 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
