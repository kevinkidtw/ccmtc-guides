"""由 data.json 產生最新消息公告用的 HTML（announcement.html）。

公告內文以 white-space: pre-wrap 顯示，所以表格必須寫在同一行，區塊之間才用換行。
名單不放選手與指導教師姓名（原始 PDF 已遮蔽，公告只需隊名與學校）；完整公告版 PDF 另以附件提供。
"""
import json, re
from collections import Counter, OrderedDict

EVENT = {'energy': '物資能源爭霸戰', 'target': '標靶爭奪賽'}
GROUP = {'es-r': '國小偏鄉組', 'es-g': '國小一般組', 'jh-r': '國中偏鄉組', 'jh-g': '國中一般組'}
MEDAL = {'特優': '🥇 特優', '優等': '🥈 優等', '甲等': '🥉 甲等', '佳作': '佳作'}
HOME = '屏東縣'  # 本屆屏東縣得獎隊伍皆為恆春半島（屏南地區）學校

TH = 'style="padding:8px;text-align:left"'
TD = 'style="padding:8px"'
TD_NOWRAP = 'style="padding:8px;white-space:nowrap"'


def short(s):
    s = re.sub(r'^(屏東縣|高雄市|臺東縣|臺南市)立?', '', s)
    s = re.sub(r'^\S{1,3}?[鄉鎮區市](?=\S{3,})', '', s)
    return s.replace('國民中學', '國中').replace('國民小學', '國小')


def table(head, rows, highlight=None):
    th = ''.join(f'<th {TH}>{h}</th>' for h in head)
    body = ''
    for r in rows:
        bg = ';background:#fffbeb' if highlight and highlight(r) else ''
        # 第一欄（獎項）不換行，手機上才不會擠成「特／優」
        cells = ''.join(f'<td {TD_NOWRAP if i == 0 else TD}>{c}</td>' for i, c in enumerate(r['cells']))
        body += f'<tr style="border-top:1px solid #e2e8f0{bg}">{cells}</tr>'
    return (f'<table style="width:100%;border-collapse:collapse;font-size:15px;white-space:normal">'
            f'<thead><tr style="background:#fef0c7">{th}</tr></thead><tbody>{body}</tbody></table>')


def main():
    data = json.load(open('data.json', encoding='utf-8'))
    home = [r for r in data if r['c'] == HOME]
    top = [r for r in home if r['a'] != '佳作']
    order = {'特優': 0, '優等': 1, '甲等': 2}
    top.sort(key=lambda r: order[r['a']])
    cnt = Counter(r['a'] for r in home)
    schools = OrderedDict()
    for r in home:
        schools.setdefault(short(r['s']), 0)
    merit = Counter(short(r['s']) for r in home if r['a'] == '佳作')
    by_event = Counter(r['e'] for r in data)

    out = []
    out.append(
        f'恭喜屏南地區各校選手！「2026 全國 AI 智創機器人競賽－扶輪盃」得獎名單已公布。'
        f'本屆共 <b>{len(data)} 隊</b>獲獎（{EVENT["energy"]} {by_event["energy"]} 隊、{EVENT["target"]} {by_event["target"]} 隊），'
        f'屏南地區 {len(schools)} 校共獲 <b>{len(home)} 項次</b>，其中<b>特優 {cnt["特優"]}、優等 {cnt["優等"]}、甲等 {cnt["甲等"]}</b>。')
    out.append('')
    out.append('<b>🏆 屏南地區前三名</b>')
    out.append(table(['獎項', '賽事・組別', '隊伍', '學校'], [
        {'cells': [MEDAL[r['a']], f'{EVENT[r["e"]]}<br>{GROUP[r["g"]]}', f'<b>{r["t"]}</b>', short(r['s'])]} for r in top]))
    out.append('另有佳作 {} 隊（{}）。'.format(
        cnt['佳作'], '、'.join(f'{k} {v}' for k, v in merit.items())))
    out.append('')

    parts = []
    for e in EVENT:
        for g in GROUP:
            rows = [r for r in data if r['e'] == e and r['g'] == g]
            if not rows:
                continue
            parts.append(f'<p style="margin:14px 0 6px;font-weight:700">{EVENT[e]}｜{GROUP[g]}</p>' + table(
                ['獎項', '隊伍', '學校', '縣市'],
                [{'cells': [MEDAL[r['a']], r['t'], short(r['s']), r['c']], 'home': r['c'] == HOME} for r in rows],
                highlight=lambda x: x['home']))
    out.append(
        '<details><summary style="cursor:pointer;font-weight:800">📋 完整得獎名單（{} 隊，依賽事與組別；黃底為屏南地區）</summary>{}</details>'
        .format(len(data), ''.join(parts)))
    out.append('')
    out.append('📎 官方公告版名單（PDF）請見下方附件。')
    open('announcement.html', 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
