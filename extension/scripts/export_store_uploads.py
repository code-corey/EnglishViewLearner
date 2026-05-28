#!/usr/bin/env python3
"""Export Chrome Web Store listing images (no alpha, correct sizes)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / 'pic' / 'store'
UPLOAD = STORE / 'upload'
ICON_SRC = ROOT / 'extension' / 'icons' / 'icon128.png'

BG_RGB = (20, 20, 24)
JPEG_QUALITY = 92

SCREENSHOT_SIZE = (1280, 800)
SMALL_PROMO_SIZE = (440, 280)
MARQUEE_SIZE = (1400, 560)
ICON_SIZE = (128, 128)


def flatten(img: Image.Image, size: tuple[int, int] | None = None, bg: tuple[int, int, int] = BG_RGB) -> Image.Image:
    """Composite RGBA onto opaque background; optionally letterbox to exact size."""
    src = img.convert('RGBA')
    if size is None:
        canvas = Image.new('RGB', src.size, bg)
        canvas.paste(src, mask=src.split()[3])
        return canvas

    fitted = ImageOps.contain(src, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', size, bg)
    ox = (size[0] - fitted.width) // 2
    oy = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (ox, oy), fitted.split()[3])
    return canvas


def save_jpeg(img: Image.Image, path: Path) -> None:
    rgb = img.convert('RGB')
    rgb.save(path, format='JPEG', quality=JPEG_QUALITY, optimize=True)
    print(f'Wrote {path} ({rgb.size[0]}x{rgb.size[1]} JPEG)')


def save_png_rgb(img: Image.Image, path: Path) -> None:
    rgb = img.convert('RGB')
    rgb.save(path, format='PNG')
    print(f'Wrote {path} ({rgb.size[0]}x{rgb.size[1]} PNG)')


def export_icon() -> None:
    if not ICON_SRC.exists():
        raise FileNotFoundError(f'Missing icon: {ICON_SRC}')
    icon = Image.open(ICON_SRC)
    out = flatten(icon, ICON_SIZE)
    save_png_rgb(out, UPLOAD / 'store-icon-128x128.png')


def export_screenshots() -> None:
    mapping = [
        ('screenshot-1-page.png', 'screenshot-1-page-1280x800.jpg'),
        ('screenshot-2-popup.png', 'screenshot-2-popup-1280x800.jpg'),
        ('screenshot-3-panel.png', 'screenshot-3-panel-1280x800.jpg'),
    ]
    for src_name, dst_name in mapping:
        src = STORE / src_name
        if not src.exists():
            print(f'Skip missing {src}')
            continue
        save_jpeg(flatten(Image.open(src), SCREENSHOT_SIZE), UPLOAD / dst_name)


def export_promos() -> None:
    small = STORE / 'promo-tile-440x280.png'
    if small.exists():
        save_jpeg(flatten(Image.open(small), SMALL_PROMO_SIZE), UPLOAD / 'promo-small-440x280.jpg')

    marquee = STORE / 'promo-marquee-1400x560.png'
    if marquee.exists():
        save_jpeg(flatten(Image.open(marquee), MARQUEE_SIZE), UPLOAD / 'promo-marquee-1400x560.jpg')


def main() -> None:
    UPLOAD.mkdir(parents=True, exist_ok=True)
    export_icon()
    export_screenshots()
    export_promos()
    print(f'\nUpload files ready in: {UPLOAD}')


if __name__ == '__main__':
    main()
