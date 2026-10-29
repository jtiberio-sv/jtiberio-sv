"""Extrai o T do peito em Braille (pixels saturados e claros dentro da caixa do logo)."""
import sys, json, colorsys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB').crop((209, 226, 292, 296))
COLS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
dw = COLS * 2; dh = round(im.height * dw / im.width); dh += (-dh) % 4
from PIL import ImageFilter
big = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
m = Image.new('L', big.size)
m.putdata([255 if (lambda h, l, s: s > 0.45 and l > 0.38)(*colorsys.rgb_to_hls(*(c / 255 for c in p))) else 0
           for p in big.get_flattened_data()])
m = m.filter(ImageFilter.MinFilter(13)).filter(ImageFilter.MaxFilter(13))  # some a borda fina do escudo
sm = m.resize((dw, dh), Image.BILINEAR)
def on(x, y):
    return sm.getpixel((x, y)) > 110
BITS = ((0, 0, 1), (0, 1, 2), (0, 2, 4), (1, 0, 8), (1, 1, 16), (1, 2, 32), (0, 3, 64), (1, 3, 128))
rows = []
for cy in range(dh // 4):
    rows.append(''.join(chr(0x2800 + sum(b for dx, dy, b in BITS if on(cx * 2 + dx, cy * 4 + dy))) for cx in range(COLS)))
json.dump(rows, sys.stdout, ensure_ascii=False)
