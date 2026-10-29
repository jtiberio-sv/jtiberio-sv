# Tyber em Braille

Gera `assets/tyber.svg`: o personagem convertido em caracteres Braille, com boot linha a linha,
visor pulsando, logo em gradiente e scanline/glitch — tudo CSS/SMIL dentro do SVG (o GitHub não roda JS).

```bash
python3 braille.py tyber.jpg 84 tyber-alpha.png > /tmp/art.json   # robô (máscara gerada com rembg isnet-general-use)
python3 logo.py tyber.jpg 30 > /tmp/logo.json                      # T do peito
python3 gen_svg.py /tmp/art.json /tmp/logo.json ../../assets/tyber.svg
```
