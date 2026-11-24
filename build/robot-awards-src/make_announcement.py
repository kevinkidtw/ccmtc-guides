"""由 data.json 產生最新消息公告用的 HTML（announcement.html）。

公告內文以 white-space: pre-wrap 顯示，所以表格必須寫在同一行，區塊之間才用換行。
只列屏南地區（屏東縣）隊伍，其他縣市不列；名單不放選手與指導教師姓名。完整公告版 PDF 另以附件提供。
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


def table(head, rows, nowrap_first=False):
    th = ''.join(f'<th {TH}>{h}</th>' for h in head)
    body = ''
    for r in rows:
        # 第一欄（獎項）不換行，手機上才不會擠成「特／優」
        cells = ''.join(f'<td {TD_NOWRAP if nowrap_first and i == 0 else TD}>{c}</td>' for i, c in enumerate(r['cells']))
        body += f'<tr style="border-top:1px solid #e2e8f0">{cells}</tr>'
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

    out = []
    out.append(
        f'恭喜屏南地區各校選手！「2026 全國 AI 智創機器人競賽－扶輪盃」得獎名單已公布。'
        f'屏南地區 {len(schools)} 校共獲 <b>{len(home)} 項次</b>，其中<b>特優 {cnt["特優"]}、優等 {cnt["優等"]}、甲等 {cnt["甲等"]}</b>。')
    out.append('')
    out.append('<b>🏆 屏南地區前三名</b>')
    out.append(table(['獎項', '賽事・組別', '隊伍', '學校'], [
        {'cells': [MEDAL[r['a']], f'{EVENT[r["e"]]}<br>{GROUP[r["g"]]}', f'<b>{r["t"]}</b>', short(r['s'])]} for r in top], nowrap_first=True))
    out.append('')
    merits = [r for r in home if r['a'] == '佳作']
    out.append(f'<b>🎖️ 佳作（{len(merits)} 隊）</b>')
    out.append(table(['賽事・組別', '隊伍', '學校'], [
        {'cells': [f'{EVENT[r["e"]]}<br>{GROUP[r["g"]]}', r['t'], short(r['s'])]} for r in merits]))
    out.append('')
    out.append('📎 各組完整得獎名單請見下方附件（主辦單位公告版 PDF）。')
    open('announcement.html', 'w', encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()
