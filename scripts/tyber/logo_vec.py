"""Logo T do Tyber redesenhado em vetor (coordenadas medidas no peito do robo) e convertido para Braille."""
import sys, json
from PIL import Image, ImageDraw
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
X0, Y0, X1, Y1 = 36, 112, 396, 416                     # caixa do logo no recorte 4x
POLYS = [
    [(76, 118), (290, 118), (251, 170), (48, 170)],      # barra superior
    [(42, 190), (120, 190), (120, 262)],                 # asa esquerda
    [(130, 190), (206, 190), (206, 408), (134, 372)],    # haste esquerda (chanfro embaixo)
    [(306, 118), (392, 118), (290, 252), (290, 384), (230, 412), (230, 190), (250, 190)],  # diagonal + haste direita
]
SS = 8
dw = COLS * 2
dh = round((Y1 - Y0) * dw / (X1 - X0)); dh += (-dh) % 4
sx, sy = dw * SS / (X1 - X0), dh * SS / (Y1 - Y0)
big = Image.new('L', (dw * SS, dh * SS))
d = ImageDraw.Draw(big)
for p in POLYS:
    d.polygon([((x - X0) * sx, (y - Y0) * sy) for x, y in p], fill=255)
sm = big.resize((dw, dh), Image.BOX)
on = lambda x, y: sm.getpixel((x, y)) > 120
BITS = ((0, 0, 1), (0, 1, 2), (0, 2, 4), (1, 0, 8), (1, 1, 16), (1, 2, 32), (0, 3, 64), (1, 3, 128))
rows = [''.join(chr(0x2800 + sum(b for dx, dy, b in BITS if on(cx * 2 + dx, cy * 4 + dy))) for cx in range(COLS))
        for cy in range(dh // 4)]
json.dump(rows, sys.stdout, ensure_ascii=False)
