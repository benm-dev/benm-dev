#!/usr/bin/env python3
"""Generate the proposed enclosure README from an anonymised local snapshot.

Offline only. This script never connects to GitHub or publishes changes.
"""
import base64
import hashlib
import json
from datetime import date
from html import escape
from pathlib import Path
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'enclosure'
SNAPSHOT = json.loads((ROOT / 'activity.json').read_text())
TOTAL = SNAPSHOT['records_total']
PUBLIC = sum(SNAPSHOT['public_series'])
PRIVATE = sum(SNAPSHOT['private_series'])
assert PUBLIC + PRIVATE == TOTAL == sum(SNAPSHOT['series'])
for i, n in enumerate(SNAPSHOT['series']):
    assert SNAPSHOT['public_series'][i] + SNAPSHOT['private_series'][i] == n
DATE_RANGE = f"{date.fromisoformat(SNAPSHOT['days'][0]):%d %b} – {date.fromisoformat(SNAPSHOT['days'][-1]):%d %b %Y}"

PALETTES = {
    'dark': dict(bg='#10151b', panel='#17222b', ink='#e4edf2', muted='#a5b6c2', edge='#354957', top='#3a5160', front='#253b48', side='#172a35', blue='#8acee4', blue_side='#39758c', copper='#dda57f', copper_side='#916647', faint='#202e38'),
    'light': dict(bg='#f5f7f8', panel='#e8eef2', ink='#1a2e3b', muted='#526674', edge='#a5bac7', top='#d5e2e9', front='#adc3d0', side='#86a3b6', blue='#166d8c', blue_side='#164c66', copper='#a0633d', copper_side='#70462e', faint='#dbe5eb'),
}
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

class Panel:
    def __init__(self, name, mobile, theme, height, title):
        self.name, self.mobile, self.theme = name, mobile, theme
        self.w, self.h = (360 if mobile else 736), height
        self.c = PALETTES[theme]
        self.p = 22 if mobile else 34
        self.body = []
        self.title = title
        self.copy = []

    def add(self, markup):
        self.body.append(markup)

    def text(self, x, y, value, size=18, color='ink', weight=400, depth=False, anchor=None):
        self.copy.append(value)
        anchor_attr = f' text-anchor="{anchor}"' if anchor else ''
        color = self.c.get(color, color)
        if depth:
            for offset in (1.5,.75):
                self.add(f'<text x="{x+offset}" y="{y+offset}" fill="{self.c["side"]}" font-size="{size}" font-weight="{weight}"{anchor_attr} aria-hidden="true">{escape(value)}</text>')
        self.add(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}"{anchor_attr}>{escape(value)}</text>')

    def wrap(self, x, y, value, width, size=18, color='muted', line=27):
        f = ImageFont.truetype(FONT_PATH, size)
        words = value.split()
        lines, current = [], ''
        for word in words:
            trial = f'{current} {word}'.strip()
            if current and f.getlength(trial) > width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current: lines.append(current)
        for s in lines:
            self.text(x,y,s,size,color)
            y += line
        return y

    def rule(self,y):
        self.add(f'<path d="M{self.p} {y}H{self.w-self.p}" stroke="{self.c["edge"]}"/>')

    def shape(self,points,fill,stroke=None):
        fill=self.c.get(fill,fill)
        stroke=self.c.get(stroke,stroke) if stroke else None
        path='L'.join(f'{x:.2f},{y:.2f}' for x,y in points)
        self.add(f'<path d="M{path}Z" fill="{fill}"'+(f' stroke="{stroke}" stroke-width=".8" stroke-linejoin="round"' if stroke else '')+'/>')

    def finish(self):
        style = '''text{font-family:DejaVu Sans,Arial,sans-serif}.flow{animation:flow 7s linear infinite}.scan{animation:scan 5s ease-in-out infinite}@keyframes flow{to{stroke-dashoffset:-160}}@keyframes scan{0%,100%{opacity:.4}50%{opacity:1}}@media(prefers-reduced-motion:reduce){.flow,.scan{animation:none}}'''
        # Background fills each asset, including readable SVG text, so GitHub cannot change its contrast.
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc"><title id="title">{escape(self.title)}</title><desc id="desc">{escape(" ".join(self.copy))}</desc><style>{style}</style><defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{self.c["top"]}"/><stop offset="1" stop-color="{self.c["front"]}"/></linearGradient></defs><rect width="100%" height="100%" fill="{self.c["bg"]}"/>'+''.join(self.body)+'</svg>'
        file=OUT / f'{self.name}-{self.theme}{"-mobile" if self.mobile else ""}.svg'
        file.write_text(svg)
        return file

def iso(x,y,z):
    return (x-y)*.86,(x+y)*.28-z

def box(p,x,y,z,w,d,h,style='metal',wire=False):
    pts = [iso(*xyz) for xyz in ((x,y,z+h),(x+w,y,z+h),(x+w,y+d,z+h),(x,y+d,z+h),(x,y,z),(x+w,y,z),(x+w,y+d,z),(x,y+d,z))]
    top,front,side = ('top','front','side') if style=='metal' else (style,style+'_side',style+'_side')
    if wire:
        for indices in ((0,1,2,3),(3,2,6,7),(1,5,6,2)):
            p.shape([pts[i] for i in indices],'none','blue')
    else:
        p.shape([pts[i] for i in (3,2,6,7)],front,'edge' if style=='metal' else None)
        p.shape([pts[i] for i in (1,5,6,2)],side,'edge' if style=='metal' else None)
        p.shape([pts[i] for i in (0,1,2,3)],'url(#metal)' if style=='metal' else top,'edge' if style=='metal' else None)

def machine(p,cx,cy,scale=1,opened=False,wire=False):
    p.add(f'<g transform="translate({cx} {cy}) scale({scale})" aria-hidden="true">')
    p.add(f'<ellipse cx="0" cy="94" rx="240" ry="21" fill="{p.c["faint"]}"/>')
    box(p,-140,-95,0,280,190,18,wire=wire)
    # Internal board and copper contact rows are deliberately geometric decoration.
    box(p,-115,-72,22,230,144,7,wire=wire)
    for x in range(-95,100,22):
        box(p,x,50,30,11,12,6,style='copper',wire=wire)
    if opened:
        for x,y,w,d,h in [(-80,-42,56,40,22),(3,-42,75,35,15),(-68,12,49,18,11),(7,7,65,23,16)]:
            box(p,x,y,31,w,d,h,wire=wire)
        # Lifted wireframe or solid lid, always in the same coordinate system.
        box(p,-148,-103,126,296,206,12,wire=wire)
    else:
        box(p,-148,-103,62,296,206,13,wire=wire)
    lid_z = 138 if opened else 75
    for x,y in [(-126,-80),(126,-80),(-126,80),(126,80)]:
        sx,sy=iso(x,y,lid_z)
        p.add(f'<ellipse cx="{sx}" cy="{sy}" rx="4.5" ry="1.6" fill="{p.c["side"]}" stroke="{p.c["edge"]}"/>')
    if not wire:
        a,b,c,d=(*iso(-65,-27,lid_z),*iso(65,-27,lid_z))
        p.add(f'<path d="M{a} {b}L{c} {d}" stroke="{p.c["blue"]}" stroke-width="2"/>')
        for yy in range(-5,35,10):
            a,b=iso(-65,yy,lid_z);c,d=iso(25,yy,lid_z)
            p.add(f'<path d="M{a} {b}L{c} {d}" stroke="{p.c["edge"]}" stroke-width="2"/>')
        route=[iso(-115,78,18),iso(95,78,18),iso(95,-60,18)]
        p.add('<path d="M'+'L'.join(f'{x},{y}' for x,y in route)+f'" fill="none" stroke="{p.c["blue"]}" stroke-width="2" stroke-dasharray="18 142" class="flow"/>')
    p.add('</g>')

def identity(m,t):
    p=Panel('identity',m,t,168 if m else 136,'Ben Marshall — Sydney. Systems, interfaces and developer tools.')
    p.text(p.p,34,'BENM-DEV / SYDNEY',14,'muted')
    p.text(p.p,89,'Ben Marshall',37 if m else 47,weight=500,depth=True)
    p.wrap(p.p,126,'Linux systems. Remote interfaces. Developer tools.',p.w-2*p.p,17 if m else 18,line=26)
    return p

def cover(m,t):
    p=Panel('cover',m,t,300 if m else 345,'Open the enclosure to explore work, input and activity.')
    machine(p,p.w/2,131 if m else 169,.70 if m else 1.06)
    p.text(p.p,p.h-43,'Open the enclosure',23 if m else 27,weight=500,depth=True)
    p.text(p.p,p.h-15,'Work · input · activity',16,'muted')
    return p

def summary(name,m,t,index,title,sub):
    p=Panel(name,m,t,94 if m else 82,f'{title}. {sub}. Expand or collapse this panel.')
    p.rule(1)
    p.text(p.p,30,index,14,'copper')
    p.text(p.p+39,31,title,19 if m else 23,weight=500,depth=True)
    p.wrap(p.p+39,59,sub,p.w-p.p*2-39,15 if m else 16,line=23)
    return p

def work(m,t):
    p=Panel('work',m,t,758 if m else 600,'Current work: systems, interfaces, developer tooling and architecture in progress.')
    sections=[
        ('Systems','Reproducible Linux workstations, declarative configuration, Wayland desktops and remote access.'),
        ('Interfaces','Desktop streaming for foldable devices, touch input and on-screen typing. Broader keyboard integration is in development.'),
        ('Developer tooling','Application compatibility, agent and IDE integration, and automation around the workstation.'),
        ('Exploring','An OS component model connecting configuration, capabilities, ownership and runtime evidence. Architecture in progress.'),
    ]
    for i,(title,copy) in enumerate(sections):
        y=23+i*(174 if m else 129)
        if m:
            p.text(p.p,y+23,title,23,weight=500,depth=True)
            p.wrap(p.p,y+54,copy,p.w-2*p.p,17,line=26)
        else:
            p.add(f'<g transform="translate(96 {y+62}) scale(.63)" aria-hidden="true">')
            box(p,-66,-41,0,132,82,14)
            box(p,-40,-19,20+6*i,80,38,8,style='blue' if i<3 else 'copper')
            p.add('</g>')
            p.text(184,y+26,title,24,weight=500,depth=True)
            p.wrap(184,y+57,copy,p.w-218,18,line=28)
        if i<3:p.rule(y+(160 if m else 119))
    p.text(p.p,p.h-31,'RUST · SWIFT · NIX',15,'muted')
    if m:p.text(p.p,p.h-9,'TYPESCRIPT · WAYLAND · PYTHON',15,'muted')
    else:p.text(241,p.h-31,'TYPESCRIPT · WAYLAND · PYTHON',15,'muted')
    return p

def signal(m,t):
    p=Panel('signal',m,t,585 if m else 447,'A conceptual touch input path through the remote session, compositor and application.')
    p.text(p.p,31,'REMOTE INPUT / CONCEPTUAL PATH',14,'muted')
    if m:
        positions=[(82,112),(257,112),(257,240),(82,240)]
        route='M82 140H257V265H82'
    else:
        positions=[(104,115),(280,115),(456,115),(632,115)]
        route='M104 145H632'
    p.add(f'<path d="{route}" fill="none" stroke="{p.c["edge"]}"/>')
    p.add(f'<path d="{route}" fill="none" stroke="{p.c["blue"]}" stroke-width="2" stroke-dasharray="18 142" class="flow"/>')
    for i,(x,y) in enumerate(positions):
        p.add(f'<g transform="translate({x} {y}) scale(.72)" aria-hidden="true">')
        box(p,-62,-34,0,124,68,11)
        box(p,-32,-18,19,64,36,8,style='blue')
        p.add('</g>')
        p.text(x,y+57,['Input','Session','Compositor','App'][i],17,'ink',anchor='middle')
    start=335 if m else 211
    entries=[('01 / Input','Touch begins on the foldable display.'),('02 / Session','The connection identifies its desktop session.'),('03 / Compositor','Focus and coordinates resolve to a surface.'),('04 / Application','The app receives the input it supports.')]
    y=start
    for label,desc in entries:
        p.text(p.p,y,label,17,weight=500)
        y=p.wrap(p.p,y+24,desc,p.w-2*p.p,15 if m else 17,line=23)+16
    p.h=y+12
    return p

def lattice(p,series,cx,cy,scale,color):
    p.add(f'<g transform="translate({cx} {cy}) scale({scale})" aria-hidden="true">')
    box(p,-88,-77,-8,176,154,6)
    # One pillar per day. Linear, shared height scale: 0..snapshot maximum.
    for row,col in sorted(((r,c) for r in range(7) for c in range(8)),key=lambda q:sum(q)):
        day=col*7+row
        n=series[day]
        if n:
            box(p,-85+col*22,-74+row*22,0,15,15,n*.46,style=color)
        else:
            a,b=iso(-85+col*22,-74+row*22,0)
            p.add(f'<ellipse cx="{a}" cy="{b}" rx="2.1" ry=".9" fill="{p.c["edge"]}"/>')
    p.add('</g>')

def public(m,t):
    p=Panel('public',m,t,370 if m else 296,'Public activity: 38 recorded actions in a 56-day snapshot. Each pillar is one day.')
    p.text(p.p,35,DATE_RANGE,15,'muted')
    p.text(p.p,109,f'{PUBLIC:,}',57 if m else 62,weight=500,depth=True)
    p.text(p.p,141,'PUBLIC ACTIONS',15,'blue')
    lattice(p,SNAPSHOT['public_series'],p.w/2 if m else 514,242 if m else 163,.90 if m else 1.15,'blue')
    p.text(p.p,p.h-66,'Daily activity',18,weight=500)
    p.wrap(p.p,p.h-39,'One pillar per day. Height = recorded actions.',p.w-2*p.p,15,line=23)
    return p

def private(m,t):
    p=Panel('private',m,t,590 if m else 448,'Public and private activity totals, with private daily activity revealed.')
    p.text(p.p,38,'THE PRIVATE LAYER',15,'copper')
    p.text(p.p,112,f'{PRIVATE:,}',53 if m else 62,weight=500,depth=True)
    p.text(p.p,143,'PRIVATE ACTIONS',15,'copper')
    lattice(p,SNAPSHOT['private_series'],p.w/2 if m else 514,268 if m else 167,.90 if m else 1.15,'copper')
    top=358 if m else 257
    p.rule(top-19)
    p.text(p.p,top,'Recorded action',15,'muted')
    a,b = ((244,337) if m else (556,702))
    p.text(a,top,'Public',15,'blue',anchor='end')
    p.text(b,top,'Private',15,'copper',anchor='end')
    for i,(key,label) in enumerate([('commits','Commits'),('pull_requests','PRs opened'),('issues','Issues opened')]):
        y=top+39+i*42
        p.text(p.p,y,label,17)
        p.text(a,y,f'{sum(SNAPSHOT["metrics"][key]["public"]):,}',18,anchor='end')
        p.text(b,y,f'{sum(SNAPSHOT["metrics"][key]["private"]):,}',18,anchor='end')
    p.rule(top+139)
    p.text(p.p,top+172,f'{TOTAL:,} total recorded actions',19,weight=500)
    if m:p.text(p.p,top+208,'56 days · aggregate counts only',15,'muted')
    return p

def scope(m,t):
    copy=[
        'Commits authored on default branches of accessible owned repositories pushed during the window. Fork duplicates count once, as public if visible in a public repository.',
        'Pull requests and issues count items I opened during the window across accessible repositories.',
        'Dates use UTC. These are snapshot records, not the GitHub contribution-calendar total. Repository names and item details are omitted.',
    ]
    p=Panel('scope',m,t,567 if m else 297,'How the activity snapshot is counted.')
    y=34
    for para in copy:
        y=p.wrap(p.p,y,para,p.w-2*p.p,17,line=26)+19
    p.h=y+10
    return p

def footer(m,t):
    p=Panel('footer',m,t,75 if m else 62,'Built from a dated, anonymised snapshot. Most current work is private.')
    p.rule(1)
    p.wrap(p.p,29,'Most current work is private. Explore the work through its systems and interfaces.',p.w-2*p.p,15,line=23)
    return p

def picture(name,alt,inline=False):
    def path(theme,mobile):
        file=OUT/f'{name}-{theme}{"-mobile" if mobile else ""}.svg'
        if inline:return 'data:image/svg+xml;base64,'+base64.b64encode(file.read_bytes()).decode()
        return './assets/enclosure/'+file.name
    return '<picture>\n'+''.join(f'<source media="{media}" srcset="{path(theme,mob)}"/>\n' for media,theme,mob in [('(max-width: 640px) and (prefers-color-scheme: dark)','dark',True),('(max-width: 640px)','light',True),('(prefers-color-scheme: dark)','dark',False)])+f'<img src="{path("light",False)}" width="100%" alt="{escape(alt,quote=True)}"/>\n</picture>'

def content(inline=False):
    img=lambda name,alt:picture(name,alt,inline)
    section=lambda head,alt,body:'<details>\n<summary>'+img(head,alt)+'</summary>\n'+body+'\n</details>\n'
    work_section=section('work-tab','What I build. Expand for systems, interfaces, developer tooling and architecture.',img('work','Systems: reproducible Linux, declarative configuration and remote access. Interfaces: foldable streaming, touch and on-screen typing. Developer tooling: compatibility, agents, IDE integration and automation. Exploring: component ownership and runtime evidence.'))
    signal_section=section('signal-tab','Follow a touch. Expand a conceptual remote input path.',img('signal','Conceptual path: touch input, connected session, compositor focus and application input.'))
    scope_section=section('scope-tab','What is counted. Expand the scope of the activity snapshot.',img('scope',SNAPSHOT['scope']+' '+SNAPSHOT['coverage']))
    metric_alt=' '.join(f'{label}: {sum(SNAPSHOT["metrics"][key]["public"]):,} public and {sum(SNAPSHOT["metrics"][key]["private"]):,} private.' for key,label in [('commits','Commits'),('pull_requests','Pull requests opened'),('issues','Issues opened')])
    private_section=section('private-tab',f'Lift the private layer. Reveal {PRIVATE:,} private recorded actions.',img('private',f'{PRIVATE:,} private actions; {TOTAL:,} total. '+metric_alt)+scope_section)
    activity_section=section('activity-tab','Look below the surface. Open the public and private activity snapshot.',img('public',f'{PUBLIC:,} public actions. {DATE_RANGE}. One pillar for each of 56 days.')+private_section)
    return img('identity','Ben Marshall, Sydney. Linux systems, remote interfaces and developer tools.')+'\n<details'+(' open' if inline else '')+'>\n<summary>'+img('cover','Open the enclosure. Explore work, input and activity.')+'</summary>\n'+work_section+signal_section+activity_section+'\n</details>\n'+img('footer','Most current work is private. Explore its systems and interfaces.')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    generators=[identity,cover,work,signal,public,private,scope,footer]
    titles=[('work-tab','01','What I build','Systems · interfaces · tooling'),('signal-tab','02','Follow a touch','From display to application'),('activity-tab','03','Below the surface','Public and private activity'),('private-tab','↓','Lift the private layer','Reveal the aggregate counts'),('scope-tab','?','What is counted','Scope of the dated snapshot')]
    for m in (False,True):
        for theme in PALETTES:
            for make in generators:make(m,theme).finish()
            for name,index,title,sub in titles:summary(name,m,theme,index,title,sub).finish()
    (ROOT/'README.md').write_text(content()+'\n')
    (OUT/'manifest.json').write_text(json.dumps({'schema':1,'input_sha256':hashlib.sha256((ROOT/'activity.json').read_bytes()).hexdigest(),'window':{'from':SNAPSHOT['days'][0],'to':SNAPSHOT['days'][-1]},'counts':{'public':PUBLIC,'private':PRIVATE,'total':TOTAL},'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.svg'))}},indent=2)+'\n')
    print(f'{len(list(OUT.glob("*.svg")))} SVGs; counts {PUBLIC} + {PRIVATE} = {TOTAL}.')

if __name__=='__main__':main()
