"""Converte a imagem do Tyber em arte Braille colorida + mascara de regioes."""
import sys, json, colorsys
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SRC = sys.argv[1]
COLS = int(sys.argv[2]) if len(sys.argv) > 2 else 70
VISOR = (205, 86, 292, 106)
LOGO = (208, 224, 294, 298)

im = Image.open(SRC).convert('RGB')
W, H = im.size

# --- mascara: alpha do rembg (isnet-general-use), gerado uma vez e versionado ---
lum = im.convert('L')
fg = Image.open(sys.argv[3] if len(sys.argv) > 3 else 'alpha.png').convert('L')
fg.paste(0, (0, 935, W, H))  # reflexo do chao

dw = COLS * 2
dh = round(H * dw / W)
dh += (-dh) % 4
rows = dh // 4
sx, sy = W / dw, H / dh

small = im.resize((dw, dh), Image.LANCZOS)
mask = fg.resize((dw, dh), Image.BILINEAR)
edges = ImageOps.autocontrast(lum.filter(ImageFilter.FIND_EDGES).resize((dw, dh), Image.BILINEAR))

# intensidade: brilho com piso dentro da mascara + realce de borda, dithering Floyd-Steinberg
val = [[0.0] * dw for _ in range(dh)]
for y in range(dh):
    for x in range(dw):
        m = mask.getpixel((x, y)) / 255
        if m < 0.5: continue
        r, g, b = small.getpixel((x, y))
        l = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        e = edges.getpixel((x, y)) / 255
        val[y][x] = min(1.0, 0.06 + 1.05 * l ** 0.85 + 0.55 * e)
dots = [[False] * dw for _ in range(dh)]
for y in range(dh):
    for x in range(dw):
        v = val[y][x]
        if mask.getpixel((x, y)) < 128: continue
        on = v >= 0.5
        dots[y][x] = on
        err = v - (1.0 if on else 0.0)
        for dx, dy, w in ((1, 0, 7), (-1, 1, 3), (0, 1, 5), (1, 1, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < dw and ny < dh and mask.getpixel((nx, ny)) >= 128:
                val[ny][nx] += err * w / 16

BITS = ((0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80))

def boost(rgb):
    """Realca e quantiza em HLS (quantizar em RGB desviava o laranja para vermelho)."""
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    if h < 0.13 or h > 0.95: h = max(0.06, (h + 0.02) % 1 if h < 0.13 else 0.06)  # laranja Tyber
    l = max(0.48, min(0.72, l * 1.1 + 0.18)); s = min(1, s * 1.2)
    h = round(h * 36) / 36; l = round(l / 0.08) * 0.08; s = round(s / 0.2) * 0.2
    r, g, b = colorsys.hls_to_rgb(h % 1, l, s)
    return '#%02x%02x%02x' % tuple(min(255, round(c * 255)) for c in (r, g, b))

def inside(box, x, y):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]

out = []
for cy in range(rows):
    row = []
    for cx in range(COLS):
        code, cols_ = 0, []
        for dx, dy, bit in BITS:
            x, y = cx * 2 + dx, cy * 4 + dy
            if dots[y][x]:
                code |= bit; cols_.append(small.getpixel((x, y)))
        if not code:
            row.append([' ', None, '']); continue
        avg = tuple(sum(c[i] for c in cols_) // len(cols_) for i in range(3))
        ox, oy = (cx * 2 + 1) * sx, (cy * 4 + 2) * sy
        h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in avg))
        tag = ''
        if inside(VISOR, ox, oy) and 0.45 < h < 0.8: tag = 'v'
        elif inside(LOGO, ox, oy) and s > 0.35 and l > 0.3 and not (0.02 < h < 0.1): tag = 'l'
        row.append([chr(0x2800 + code), boost(avg), tag])
    out.append(row)
json.dump({'cols': COLS, 'rows': rows, 'cells': out}, sys.stdout)
