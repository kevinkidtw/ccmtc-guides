import json,base64,html
D=json.load(open('data.json'))
EV={'soccer':'無人機足球賽','ring':'無人機穿環任務賽','prog':'無人機程控任務賽','sim':'無人機虛擬飛行技能挑戰賽'}
EVS={'soccer':'足球賽','ring':'穿環任務賽','prog':'程控任務賽','sim':'虛擬飛行技能挑戰賽'}
G={'jh':'國中組','es':'國小組'}
R={1:'金',2:'銀',3:'銅'}
ORDER=['車城國中','滿州國中','恆春國小','水泉國小龍泉分校','墾丁國小','墾丁國小鵝鑾分校','加祿國小']
css=open('poster_common.css').read()
qr='data:image/svg+xml;base64,'+base64.b64encode(open('qr.svg','rb').read()).decode()
e=html.escape
FLIGHT='''<svg class="flight" style="right:-30px;top:40px;width:560px" viewBox="0 0 560 360" fill="none">
<path d="M10 320 C 140 300, 170 180, 280 170 S 440 90, 540 40" stroke="#f2b705" stroke-width="3" stroke-dasharray="2 11" stroke-linecap="round" opacity=".8"/>
<ellipse cx="190" cy="236" rx="17" ry="42" stroke="#f2b705" stroke-width="6" opacity=".5"/>
<ellipse cx="350" cy="140" rx="15" ry="36" stroke="#f2b705" stroke-width="6" opacity=".75"/>
<g transform="translate(450 78) rotate(-14)"><rect x="-26" y="-9" width="52" height="18" rx="9" fill="#f2b705"/>
<path d="M-24 -4 L-52 -22 M24 -4 L52 -22 M-24 4 L-52 22 M24 4 L52 22" stroke="#e5e9f2" stroke-width="4" stroke-linecap="round"/>
<g fill="none" stroke="#e5e9f2" stroke-width="2.5"><ellipse cx="-52" cy="-22" rx="22" ry="6"/><ellipse cx="52" cy="-22" rx="22" ry="6"/><ellipse cx="-52" cy="22" rx="22" ry="6"/><ellipse cx="52" cy="22" rx="22" ry="6"/></g></g></svg>'''

# ---------- poster 1 ----------
med=sorted([d for d in D if d['r']<4],key=lambda d:(d['r'],d['g']!='jh'))
cards=''.join(f'''<div class="card r{d['r']}"><div class="disc">{R[d['r']]}</div><div>
<div class="ev">{EV[d['e']]}</div><div class="tm">{e(d['t'])}</div>
<div class="sc">{e(d['s'])} <span class="tag {d['g']}">{G[d['g']]}</span></div></div></div>''' for d in med)
tal=[]
for s in ORDER:
    r=[sum(1 for d in D if d['s']==s and d['r']==k) for k in (1,2,3,4)]
    tal.append((s,r))
tal.sort(key=lambda x:(-x[1][0],-x[1][1],-x[1][2],-x[1][3]))
cols=['#f0b400','#a7b2c1','#c37936']
rows=''.join(f'''<div class="srow"><span class="sn">{e(s)}</span><span class="dots">{''.join(f'<i style="background:{cols[i]}"></i>'*r[i] for i in range(3))}</span><span class="hn">佳作 {r[3]}</span><b>{sum(r)}</b></div>''' for s,r in tal)
p1=f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}
.p{{width:1080px;height:1350px}} .in{{padding:64px 68px 56px}}
.eyebrow{{font-size:22px}} h1{{font-size:86px;margin:20px 0 8px}} .sub{{font-size:38px;font-weight:800;color:#e5e9f2}}
.meta{{font-size:24px;margin-top:14px}}
.grid6{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:30px}}
.card{{background:#fff;color:#1f2937;border-radius:20px;padding:15px 20px;display:flex;gap:16px;align-items:center;border:3px solid transparent}}
.card.r1{{border-color:#f5cf55}}.card.r2{{border-color:#cdd5df}}.card.r3{{border-color:#e7b98f}}
.disc{{flex:0 0 auto;width:64px;height:64px;border-radius:50%;display:grid;place-items:center;font-weight:900;font-size:26px;color:#fff;box-shadow:inset 0 -5px 0 rgba(0,0,0,.15)}}
.r1 .disc{{background:linear-gradient(145deg,#ffd54a,#e39b00)}}.r2 .disc{{background:linear-gradient(145deg,#dfe5ec,#8794a6)}}.r3 .disc{{background:linear-gradient(145deg,#eaa66a,#a65a1f)}}
.ev{{font-size:17px;font-weight:700;color:#64748b}} .tm{{font-size:32px;font-weight:900;line-height:1.2}} .sc{{font-size:19px;font-weight:700;color:#334155}} .sc .tag{{font-size:15px;margin-left:6px}}
.board{{margin-top:18px;margin-bottom:20px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:20px;padding:12px 24px 10px;display:grid;grid-template-columns:1fr 1fr;column-gap:36px}}
.board h3{{grid-column:1/-1;font-size:20px;color:#f2b705;font-weight:900;margin-bottom:4px;letter-spacing:.06em}}
.srow{{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.08);font-size:20px}}
.srow .sn{{font-weight:800}} .dots{{display:flex;gap:4px}} .dots i{{width:14px;height:14px;border-radius:50%;display:block}}
.srow .hn{{margin-left:auto;color:#aab5c8;font-size:17px}} .srow b{{width:40px;text-align:right;color:#f2b705;font-size:22px}}
.foot{{margin-top:auto}} .qr img{{width:118px;height:118px}} .foot .t b{{font-size:26px}} .foot .t span{{font-size:19px}} .org{{font-size:17px}} .org b{{font-size:22px}}
</style></head><body><div class="p"><div class="grid"></div>{FLIGHT}<div class="in">
<span class="eyebrow">得獎榮譽榜 · 屏南地區</span>
<h1>2026 屏東縣<br><span class="hl">無人機競賽</span></h1>
<div class="sub">屏南地區國中小 得獎名單</div>
<div class="meta">115.11.20–21　南州國中體育館　｜　屏南 7 校・79 項次獲獎</div>
<div class="grid6">{cards}</div>
<div class="board"><h3>學校成績</h3>{rows}</div>
<div class="foot"><div class="qr"><img src="{qr}"></div><div class="t"><b>完整得獎名單</b><span>掃描 QR code 或前往<br>ccmtc.mooo.com/drone-awards</span></div>
<div class="org"><b>車城自造教育科技中心</b>CCMTC · 恭喜所有得獎隊伍！</div></div>
</div></div></body></html>'''
open('out/p1.html','w').write(p1)

# ---------- poster 2 (full list) ----------
def block(ev):
    out=''
    for g in ('jh','es'):
        items=[d for d in D if d['e']==ev and d['g']==g]
        tops=''.join(f'<div class="top r{d["r"]}"><span class="pill">{R[d["r"]]}牌</span><b>{e(d["t"])}</b><span>{e(d["s"])}</span></div>' for d in sorted([d for d in items if d['r']<4],key=lambda d:d['r']))
        hon=''
        for s in ORDER:
            ts=[d['t'] for d in items if d['r']==4 and d['s']==s]
            if ts: hon+=f'<div class="hs"><span class="hsn">{e(s)}</span>{"".join(f"<i>{e(t)}</i>" for t in ts)}</div>'
        out+=f'<div class="gc"><div class="gh"><span class="tag {g}">{G[g]}</span><small>{len(items)} 隊</small></div>{tops}{("<div class=hl2>佳作</div>"+hon) if hon else ""}</div>'
    n=sum(1 for d in D if d['e']==ev)
    return f'<div class="evb"><div class="eh"><h2>{EV[ev]}</h2><small>{n} 項次</small></div><div class="gcs">{out}</div></div>'
blocks=''.join(block(k) for k in EV)
p2=f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}
.p{{width:1240px;height:1754px}} .in{{padding:56px 60px 46px}}
.eyebrow{{font-size:20px}} h1{{font-size:64px;margin:18px 0 6px}} .meta{{font-size:22px}}
.flight{{width:440px!important;top:20px!important}}
.evs{{margin-top:30px;display:flex;flex-direction:column;gap:18px}}
.evb{{background:#fff;color:#1f2937;border-radius:18px;padding:18px 22px 18px}}
.eh{{display:flex;align-items:baseline;gap:12px;border-left:7px solid #f2b705;padding-left:12px;margin-bottom:8px}}
.eh h2{{font-size:28px;font-weight:900}} .eh small{{color:#64748b;font-size:16px;font-weight:700}}
.gcs{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.gh{{display:flex;align-items:center;gap:10px;margin-bottom:6px}} .gh .tag{{font-size:15px}} .gh small{{color:#64748b;font-size:14px;font-weight:700}}
.top{{display:flex;align-items:center;gap:10px;padding:7px 12px;border-radius:10px;margin-bottom:6px;font-size:21px}}
.top.r1{{background:#fff3c4}}.top.r2{{background:#edf1f5}}.top.r3{{background:#fbe8d6}}
.top .pill{{color:#fff;font-size:14px;font-weight:900;padding:2px 9px;border-radius:999px}}
.top.r1 .pill{{background:#e8a400}}.top.r2 .pill{{background:#8a97a8}}.top.r3 .pill{{background:#b86a2c}}
.top span:last-child{{margin-left:auto;color:#475569;font-size:15px;font-weight:700}}
.hl2{{font-size:13px;font-weight:900;color:#94a3b8;letter-spacing:.1em;margin:4px 0 2px}}
.hs{{display:flex;flex-wrap:wrap;align-items:center;gap:5px 6px;margin:4px 0;font-size:17px;line-height:1.4}}
.hsn{{font-weight:900;color:#334155;margin-right:4px}}
.hs i{{font-style:normal;background:#f1f5f9;border-radius:6px;padding:1px 7px;font-weight:600}}
.foot{{margin-top:auto;padding-top:20px}} .qr img{{width:104px;height:104px}} .foot .t b{{font-size:24px}} .foot .t span{{font-size:18px}} .org{{font-size:16px}} .org b{{font-size:21px}}
</style></head><body><div class="p"><div class="grid"></div>{FLIGHT}<div class="in">
<span class="eyebrow">完整得獎名單 · 屏南地區</span>
<h1>2026 屏東縣 <span class="hl">無人機競賽</span></h1>
<div class="meta">115.11.20–21　南州國中體育館　｜　屏南 7 校・79 項次獲獎</div>
<div class="evs">{blocks}</div>
<div class="foot"><div class="qr"><img src="{qr}"></div><div class="t"><b>線上榜單（可搜尋隊名）</b><span>ccmtc.mooo.com/drone-awards</span></div>
<div class="org"><b>車城自造教育科技中心</b>名單如有疑義，以主辦單位公告為準</div></div>
</div></div></body></html>'''
open('out/p2.html','w').write(p2)
