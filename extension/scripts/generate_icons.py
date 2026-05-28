#!/usr/bin/env python3
"""Generate extension icons matching the purple E logo style."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZES = (16, 32, 48, 128)
BG = (20, 20, 24, 255)
RING = (168, 85, 247, 255)
LETTER = (240, 171, 252, 255)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path('C:/Windows/Fonts/segoeuib.ttf'),
        Path('C:/Windows/Fonts/arialbd.ttf'),
        Path('C:/Windows/Fonts/msyhbd.ttc'),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_icon(size: int) -> Image.Image:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    inset = max(1, size // 16)
    ring = max(1, size // 17)
    draw.ellipse(
        (inset, inset, size - inset - 1, size - inset - 1),
        fill=BG,
        outline=RING,
        width=ring,
    )

    font_size = max(8, int(size * 0.46))
    font = load_font(font_size)
    letter = 'E'
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2 - bbox[0]
    y = (size - text_h) / 2 - bbox[1]
    draw.text((x, y), letter, fill=LETTER, font=font)
    return img


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / 'icons'
    out_dir.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        path = out_dir / f'icon{size}.png'
        draw_icon(size).save(path, format='PNG')
        print(f'Wrote {path}')


if __name__ == '__main__':
    main()
