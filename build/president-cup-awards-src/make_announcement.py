"""由 data.json 產生「115 年總統盃 AI 素養爭霸賽」屏南地區榮譽榜公告 HTML（announcement.html）。

全國賽，版面比一般公告醒目：頂部橫幅 + 每隊一張獎項卡片。
只列屏南地區隊伍、不放學生與指導教師姓名、不附 PDF（同扶輪盃公告的做法）。
公告內文以 white-space: pre-wrap 顯示，所以所有 HTML 都寫在同一行。
"""
import json

STYLE = {
    '金獎': ('🥇', 'linear-gradient(135deg,#fde68a,#f59e0b)', '#78350f'),
    '銀獎': ('🥈', 'linear-gradient(135deg,#f1f5f9,#94a3b8)', '#1e293b'),
    '銅獎': ('🥉', 'linear-gradient(135deg,#fed7aa,#c2410c)', '#431407'),
    '優選': ('🎖️', 'linear-gradient(135deg,#e0e7ff,#6366f1)', '#1e1b4b'),
    '佳作': ('🏅', 'linear-gradient(135deg,#dcfce7,#22c55e)', '#14532d'),
}
ORDER = list(STYLE)


def card(r, per_group):
    icon, bg, fg = STYLE[r['a']]
    big = r['a'] in ('金獎', '銀獎', '銅獎')
    rank_note = ''
    if r['a'] == '銅獎':
        top = per_group['金獎'] + per_group['銀獎'] + per_group['銅獎']
        rank_note = f'<div style="font-size:13px;opacity:.85;margin-top:2px">全國前 {top} 名</div>'
    return (
        f'<div style="flex:1 1 220px;min-width:0;border-radius:16px;overflow:hidden;'
        f'box-shadow:0 6px 18px rgba(15,23,42,.12);background:#fff;border:1px solid #e2e8f0">'
        f'<div style="background:{bg};color:{fg};padding:{"18px" if big else "12px"} 16px;text-align:center">'
        f'<div style="font-size:{"44px" if big else "30px"};line-height:1">{icon}</div>'
        f'<div style="font-size:{"24px" if big else "20px"};font-weight:900;letter-spacing:.1em;margin-top:6px">全國{r["a"]}</div>'
        f'{rank_note}</div>'
        f'<div style="padding:14px 16px;text-align:center">'
        f'<div style="font-size:20px;font-weight:800;color:#0f172a">{r["s"]}</div>'
        f'<div style="font-size:14px;color:#475569;margin-top:4px">{r["g"]}・隊伍編號 {r["no"]}</div>'
        f'</div></div>')


def main():
    d = json.load(open('data.json', encoding='utf-8'))
    home = sorted(d['home'], key=lambda r: ORDER.index(r['a']))
    per = d['awards_per_group']
    per_total = sum(per.values())
    schools = len({r['s'] for r in home})
    medals = [r for r in home if r['a'] in ('金獎', '銀獎', '銅獎')]

    banner = (
        '<div style="border-radius:18px;padding:22px 20px;color:#fff;text-align:center;'
        'background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#b45309 140%);margin:4px 0 14px">'
        '<div style="font-size:13px;letter-spacing:.25em;color:#fcd34d;font-weight:700">全國決賽 · 屏南之光</div>'
        '<div style="font-size:26px;font-weight:900;margin:8px 0 6px;line-height:1.35">115 年總統盃 AI 素養爭霸賽</div>'
        f'<div style="font-size:18px;font-weight:700">屏南地區 <span style="color:#fcd34d;font-size:30px">{len(home)}</span> 隊榮獲全國獎項</div>'
        '</div>')
    cards = ('<div style="display:flex;flex-wrap:wrap;gap:14px;margin:6px 0 4px">'
             + ''.join(card(r, per) for r in home) + '</div>')

    medal_txt = '、'.join(f'{r["s"]}在{r["g"]}榮獲<b>全國{r["a"]}</b>' for r in medals)
    intro = (
        f'賀！「115 年總統盃 AI 素養爭霸賽」全國決賽成績揭曉，屏南地區 {schools} 校 {len(home)} 隊在全國各縣市隊伍中脫穎而出：'
        f'{medal_txt}；'
        + '、'.join(r['s'] for r in home if r['a'] == '佳作') + '於國中偏鄉組雙雙獲得<b>全國佳作</b>。')
    note = (f'本賽事分國小一般、國小偏鄉、國中一般、國中偏鄉與表演賽 {len(d["groups"])} 組，'
            f'每組全國僅 {per_total} 隊獲獎（金獎 {per["金獎"]}、銀獎 {per["銀獎"]}、銅獎 {per["銅獎"]}、優選 {per["優選"]}、佳作 {per["佳作"]}）。'
            '恭喜獲獎的同學與指導老師！')
    out = [banner, intro, '', cards, '', f'<span style="color:#475569;font-size:15px">{note}</span>']
    open('announcement.html', 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
