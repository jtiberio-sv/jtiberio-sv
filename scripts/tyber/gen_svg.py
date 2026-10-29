"""Monta o SVG animado do Tyber (robo em Braille + logo T) a partir de art.json e logo.json."""
import sys, json
from xml.sax.saxutils import escape

art = json.load(open(sys.argv[1]))
logo = json.load(open(sys.argv[2]))
OUT = sys.argv[3]

CW, LH, FS = 7.2, 14.4, 12          # celula 1:2 -> pontos quadrados
BLANK = '⠀'                     # braille vazio no lugar de espaco: mesma largura em qualquer fonte
PAD = 28
cols, rows = art['cols'], art['rows']
cells = art['cells']

# remove ruido isolado do logo
lg = [list(r) for r in logo]
for y, r in enumerate(lg):
    for x, ch in enumerate(r):
        if ch == BLANK: continue
        nb = [lg[j][i] for j in range(max(0, y - 1), min(len(lg), y + 2))
              for i in range(max(0, x - 1), min(len(r), x + 2)) if (i, j) != (x, y)]
        if all(c == BLANK for c in nb): lg[y][x] = BLANK
logo = [''.join(r) for r in lg]

LS = 2.0                              # escala do logo
robot_w, robot_h = cols * CW, rows * LH
logo_cols, logo_rows = len(logo[0]), len(logo)
logo_w, logo_h = logo_cols * CW * LS, logo_rows * LH * LS
GAP = 70
W = PAD + robot_w + GAP + logo_w + PAD
H = PAD * 2 + robot_h
rx, ry = PAD, PAD
lx, ly = PAD + robot_w + GAP, PAD + (robot_h - logo_h) / 2 - 40

def row_text(r, y, layer, extra=''):
    """layer: '' base (cor por run), 'v' visor, 'l' logo do peito."""
    parts, cur, buf = [], None, []
    def flush():
        if buf:
            s = escape(''.join(buf))
            parts.append(f'<tspan fill="{cur}">{s}</tspan>' if cur else s)
    for ch, col, tag in r:
        if layer == '':
            if not col or tag: ch, col = BLANK, None
        else:
            if tag != layer: ch = BLANK
            col = None
        if ch == ' ': ch = BLANK
        if col != cur:
            flush(); cur, buf = col, []
        buf.append(ch)
    flush()
    if all(c == BLANK for c in ''.join(p for p in parts if not p.startswith('<'))) and not any(p.startswith('<') for p in parts):
        return ''
    return f'<text x="0" y="{y:.1f}" textLength="{cols * CW:.1f}" lengthAdjust="spacingAndGlyphs"{extra}>{"".join(parts)}</text>'

base, visor, chest = [], [], []
for i, r in enumerate(cells):
    y = (i + 1) * LH - 3
    d = f' style="animation-delay:{0.25 + i * 0.035:.3f}s"'
    t = row_text(r, y, '', ' class="b"' + d)
    if t: base.append(t)
    t = row_text(r, y, 'v')
    if t: visor.append(t)
    t = row_text(r, y, 'l')
    if t: chest.append(t)

boot_end = 0.25 + rows * 0.035
import re
ghost = re.sub(r'<tspan fill="[^"]+">([^<]*)</tspan>', r'\1', re.sub(r' class="b" style="[^"]+"', '', ''.join(base)))
logo_rows_svg = []
for i, line in enumerate(logo):
    y = (i + 1) * LH - 3
    d = f' style="animation-delay:{boot_end + 0.2 + i * 0.06:.3f}s"'
    logo_rows_svg.append(f'<text x="0" y="{y:.1f}" textLength="{logo_cols * CW:.1f}" lengthAdjust="spacingAndGlyphs" class="b"{d}>{escape(line)}</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Tyber">
<title>Tyber</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0b1020"/><stop offset="1" stop-color="#05070f"/>
  </linearGradient>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
    <path d="M24 0H0V24" fill="none" stroke="#1b2a4a" stroke-width="0.6" opacity="0.55"/>
  </pattern>
  <linearGradient id="tg" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{logo_cols * CW:.0f}" y2="{logo_rows * LH:.0f}" spreadMethod="reflect">
    <stop offset="0" stop-color="#22d3ee"/><stop offset="0.35" stop-color="#8b5cf6"/>
    <stop offset="0.65" stop-color="#ec4899"/><stop offset="1" stop-color="#fb923c"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0; {logo_cols * CW:.0f} {logo_rows * LH:.0f}; 0 0" dur="6s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="cg" gradientUnits="userSpaceOnUse" x1="{cols * CW * 0.4:.0f}" y1="{LH * 15:.0f}" x2="{cols * CW * 0.6:.0f}" y2="{LH * 21:.0f}" spreadMethod="reflect">
    <stop offset="0" stop-color="#22d3ee"/><stop offset="0.35" stop-color="#8b5cf6"/>
    <stop offset="0.65" stop-color="#ec4899"/><stop offset="1" stop-color="#fb923c"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0; 60 80; 0 0" dur="6s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#38bdf8" stop-opacity="0"/><stop offset="0.5" stop-color="#38bdf8" stop-opacity="0.22"/>
    <stop offset="1" stop-color="#38bdf8" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<style>
  text {{ font-family: "DejaVu Sans Mono", "Menlo", "Consolas", "Segoe UI Symbol", monospace; font-size: {FS}px; white-space: pre; }}
  .b {{ opacity: 0; animation: boot .45s ease-out forwards; }}
  @keyframes boot {{ 0% {{ opacity: 0; fill: #e0f2fe; }} 40% {{ opacity: 1; }} 100% {{ opacity: 1; }} }}
  .visor {{ fill: #38bdf8; opacity: 0; animation: visor 2.6s ease-in-out {boot_end:.2f}s infinite; }}
  @keyframes visor {{ 0%,100% {{ opacity: .55; fill: #2563eb; }} 50% {{ opacity: 1; fill: #a5f3fc; }} }}
  .chest {{ opacity: 0; animation: on .6s ease-out {boot_end * 0.45:.2f}s forwards; }}
  .logo {{ opacity: 0; animation: on .6s ease-out {boot_end:.2f}s forwards; }}
  @keyframes on {{ to {{ opacity: 1; }} }}
  .scan {{ animation: scan 7s linear {boot_end:.2f}s infinite; opacity: 0; }}
  @keyframes scan {{ 0% {{ transform: translateY(-120px); opacity: 1; }} 100% {{ transform: translateY({H:.0f}px); opacity: 1; }} }}
  .glitch {{ animation: glitch 9s steps(1) {boot_end + 2:.2f}s infinite; }}
  @keyframes glitch {{
    0%,91%,100% {{ transform: translate(0,0); }}
    92% {{ transform: translate(-3px,0) skewX(-2deg); }}
    93% {{ transform: translate(4px,1px); }}
    94% {{ transform: translate(-1px,0) skewX(1.5deg); }}
    95% {{ transform: translate(0,0); }}
  }}
  .ghost {{ opacity: 0; animation: ghost 9s steps(1) {boot_end + 2:.2f}s infinite; }}
  @keyframes ghost {{ 0%,91.5%,94.5%,100% {{ opacity: 0; }} 92% {{ opacity: .5; transform: translate(6px,0); }} 93.5% {{ opacity: .4; transform: translate(-5px,0); }} }}
  .cursor {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .b, .chest, .logo {{ animation: none; opacity: 1; }}
    .visor {{ animation: none; opacity: 1; }}
    .scan, .glitch, .ghost, .cursor {{ animation: none; }}
    .scan, .ghost {{ display: none; }}
  }}
</style>
<rect width="100%" height="100%" rx="14" fill="url(#bg)"/>
<rect width="100%" height="100%" rx="14" fill="url(#grid)"/>
<g class="glitch">
  <g transform="translate({rx},{ry})">
    <g class="ghost" fill="#ec4899">{ghost}</g>
    {''.join(base)}
    <g class="chest" fill="url(#cg)" filter="url(#glow)">{''.join(chest)}</g>
    <g class="visor" filter="url(#glow)">{''.join(visor)}</g>
  </g>
  <g transform="translate({lx:.1f},{ly:.1f}) scale({LS})">
    <g class="logo" fill="url(#tg)" filter="url(#glow)">{''.join(logo_rows_svg)}</g>
  </g>
</g>
<rect class="scan" x="0" y="0" width="100%" height="120" fill="url(#scan)"/>
</svg>
'''
open(OUT, 'w').write(svg)
print(f'{OUT}: {W:.0f}x{H:.0f}, {len(svg)/1024:.0f} KB')
