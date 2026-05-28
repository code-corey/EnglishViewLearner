#!/usr/bin/env python3
"""Generate Chrome Web Store promotional images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
PIC = ROOT / 'pic'
OUT = PIC / 'store'

BG = (20, 20, 24, 255)
BG_TOP = (28, 24, 38, 255)
RING = (168, 85, 247, 255)
LETTER = (240, 171, 252, 255)
ACCENT = (236, 72, 153, 255)
TEXT = (245, 245, 247, 255)
MUTED = (161, 161, 170, 255)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path('C:/Windows/Fonts/msyhbd.ttc') if bold else Path('C:/Windows/Fonts/msyh.ttc'),
        Path('C:/Windows/Fonts/segoeuib.ttf') if bold else Path('C:/Windows/Fonts/segoeui.ttf'),
        Path('C:/Windows/Fonts/arialbd.ttf') if bold else Path('C:/Windows/Fonts/arial.ttf'),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, ...],
    outline: tuple[int, ...] | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_logo(size: int) -> Image.Image:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    inset = max(2, size // 14)
    ring = max(2, size // 18)
    draw.ellipse(
        (inset, inset, size - inset - 1, size - inset - 1),
        fill=BG,
        outline=RING,
        width=ring,
    )
    font = load_font(max(12, int(size * 0.46)), bold=True)
    letter = 'E'
    bbox = draw.textbbox((0, 0), letter, font=font)
    x = (size - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), letter, fill=LETTER, font=font)
    return img


def gradient_bg(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new('RGBA', size, BG)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(BG_TOP[0] * (1 - t) + BG[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
    glow = Image.new('RGBA', size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((w * 0.55, -h * 0.35, w * 1.15, h * 0.55), fill=(168, 85, 247, 42))
    glow_draw.ellipse((-w * 0.2, h * 0.45, w * 0.35, h * 1.05), fill=(236, 72, 153, 28))
    return Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(radius=28)))


def fit_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(img.convert('RGBA'), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def fit_contain(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(img.convert('RGBA'), size, method=Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    ox = (size[0] - fitted.width) // 2
    oy = (size[1] - fitted.height) // 2
    canvas.alpha_composite(fitted, (ox, oy))
    return canvas


def paste_preview(base: Image.Image, preview: Image.Image, box: tuple[int, int, int, int], *, cover: bool = False) -> None:
    x0, y0, x1, y1 = box
    target_w, target_h = x1 - x0, y1 - y0
    fitted = fit_cover(preview, (target_w, target_h)) if cover else fit_contain(preview, (target_w, target_h))
    frame = Image.new('RGBA', (target_w + 8, target_h + 8), (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame)
    rounded_rect(frame_draw, (0, 0, target_w + 7, target_h + 7), 14, fill=(36, 36, 42, 255), outline=RING, width=2)
    frame.alpha_composite(fitted, (4, 4))
    shadow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    rounded_rect(shadow_draw, (x0 + 6, y0 + 8, x1 + 6, y1 + 8), 14, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    base.alpha_composite(shadow)
    base.alpha_composite(frame, (x0, y0))


def is_beige_background(r: int, g: int, b: int) -> bool:
    """Detect warm cream page background (and its soft shadow), keep UI colors."""
    if r > 245 and g > 245 and b > 245:
        return False
    lum = (r + g + b) / 3
    if lum < 125:
        return False
    if r > 160 and b > 110 and g < r * 0.72:
        return False
    if b > r + 30 and b > 140:
        return False
    return r >= g - 2 and g >= b - 8 and (r - b) >= 12


def remove_beige_background(img: Image.Image) -> Image.Image:
    """Make page background transparent, keeping the dark floating panel."""
    img = img.convert('RGBA')
    w, h = img.size
    pixels = img.load()
    removed = [[False] * w for _ in range(h)]

    def matches_bg(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        if a == 0:
            return True
        return is_beige_background(r, g, b)

    stack: list[tuple[int, int]] = []
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y))
        stack.append((w - 1, y))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or removed[y][x]:
            continue
        if not matches_bg(x, y):
            continue
        removed[y][x] = True
        pixels[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return img


def crop_to_content(img: Image.Image, padding: int = 4) -> Image.Image:
    img = img.convert('RGBA')
    bbox = img.split()[3].getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(img.width, x1 + padding)
    y1 = min(img.height, y1 + padding)
    return img.crop((x0, y0, x1, y1))


def trim_light_vertical_edges(img: Image.Image, threshold: float = 120.0) -> Image.Image:
    """Remove stray light columns (e.g. popup capture border) from left/right edges."""
    img = img.convert('RGBA')
    w, h = img.size
    if w == 0 or h == 0:
        return img

    def column_luminance(x: int) -> float:
        total = 0.0
        for y in range(h):
            r, g, b, _ = img.getpixel((x, y))
            total += (r + g + b) / 3
        return total / h

    left = 0
    while left < w and column_luminance(left) >= threshold:
        left += 1

    right = 0
    while right < w - left and column_luminance(w - 1 - right) >= threshold:
        right += 1

    if left == 0 and right == 0:
        return img
    return img.crop((left, 0, w - right, h))


def process_screenshot(src_name: str, img: Image.Image) -> Image.Image:
    if src_name == '截图2.png':
        return trim_light_vertical_edges(img)
    if src_name == '截图三.png':
        return crop_to_content(remove_beige_background(img))
    return img


def export_screenshots() -> None:
    mapping = [
        ('截图1.png', 'screenshot-1-page.png'),
        ('截图2.png', 'screenshot-2-popup.png'),
        ('截图三.png', 'screenshot-3-panel.png'),
    ]
    for src_name, dst_name in mapping:
        src = PIC / src_name
        if not src.exists():
            continue
        img = process_screenshot(src_name, Image.open(src))
        dst = OUT / dst_name
        img.save(dst, format='PNG')
        print(f'Wrote {dst}')
        if src_name in ('截图2.png', '截图三.png'):
            img.save(src, format='PNG')
            print(f'Updated {src}')


def find_preview() -> Path | None:
    store_popup = OUT / 'screenshot-2-popup.png'
    if store_popup.exists():
        return store_popup
    for name in ('截图2.png', 'screenshot-2-popup.png', 'screenshot2.png'):
        path = PIC / name
        if path.exists():
            return path
    for path in sorted(PIC.glob('*.png')):
        if 'promo' not in path.stem.lower() and path.parent == PIC:
            return path
    return None


def draw_chip(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int]:
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=font)
    chip_w = bbox[2] - bbox[0] + 16
    chip_h = 24
    rounded_rect(draw, (x, y, x + chip_w, y + chip_h), 12, fill=(45, 35, 58, 220), outline=(168, 85, 247, 120), width=1)
    draw.text((x + 8, y + 4), text, fill=LETTER, font=font)
    return chip_w, chip_h


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_w: int,
) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    current = ''
    for ch in text:
        trial = current + ch
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_left_column(draw: ImageDraw.ImageDraw, x: int, y: int, max_w: int, h: int) -> None:
    title_font = load_font(19, bold=True)
    sub_font = load_font(11, bold=False)
    tag_font = load_font(11, bold=False)
    foot_font = load_font(10, bold=False)

    title_y = y
    for line in wrap_text(draw, '沉浸式学习英语', title_font, max_w):
        draw.text((x, title_y), line, fill=TEXT, font=title_font)
        title_y += 24

    sub_y = title_y + 4
    for line in wrap_text(draw, '中文网页 · 分级沉浸式学英语', sub_font, max_w):
        draw.text((x, sub_y), line, fill=MUTED, font=sub_font)
        sub_y += 16

    chip_y = sub_y + 6
    for tag in ('A1–C1 本地词库', '悬停看中文', '完全离线'):
        _, chip_h = draw_chip(draw, (x, chip_y), tag, tag_font)
        chip_y += chip_h + 5

    draw.line([(x, h - 20), (x + 88, h - 20)], fill=ACCENT, width=3)
    draw.text((x, h - 34), 'Chrome 扩展 · v1.0.0', fill=(113, 113, 122, 255), font=foot_font)


def make_small_tile() -> Image.Image:
    w, h = 440, 280
    img = gradient_bg((w, h))

    left_w = 182
    gap = 12
    preview_x0 = left_w + gap
    preview_box = (preview_x0, 16, w - 12, h - 16)

    preview_path = find_preview()
    if preview_path:
        paste_preview(img, Image.open(preview_path), preview_box)

    divider = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dx = int(preview_x0 - 6)
    ImageDraw.Draw(divider).line([(dx, 20), (dx, h - 20)], fill=(168, 85, 247, 55), width=1)
    img = Image.alpha_composite(img, divider)
    draw = ImageDraw.Draw(img)

    img.alpha_composite(draw_logo(40), (16, 18))
    draw_left_column(draw, 16, 64, left_w - 20, h)
    return img


def make_marquee() -> Image.Image:
    w, h = 1400, 560
    img = gradient_bg((w, h))
    draw = ImageDraw.Draw(img)

    text_right = 500
    previews = [
        ('screenshot-3-panel.png', (520, 100, 680, 460), False),
        ('screenshot-2-popup.png', (700, 56, 980, 504), False),
        ('screenshot-1-page.png', (1000, 40, 1360, 520), True),
    ]
    for name, box, cover in previews:
        path = OUT / name
        if not path.exists():
            continue
        paste_preview(img, Image.open(path), box, cover=cover)

    divider = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(divider).line([(508, 32), (508, h - 32)], fill=(168, 85, 247, 60), width=2)
    img = Image.alpha_composite(img, divider)
    draw = ImageDraw.Draw(img)

    img.alpha_composite(draw_logo(80), (48, 48))
    draw.text((148, 54), '沉浸式学习英语', fill=TEXT, font=load_font(46, bold=True))

    sub_y = 128
    for line in wrap_text(draw, '在中文网页阅读中，按 CEFR 等级自然接触英文词汇', load_font(22), text_right - 48):
        draw.text((48, sub_y), line, fill=MUTED, font=load_font(22))
        sub_y += 30

    y = max(sub_y + 12, 200)
    for bullet in (
        'Oxford A1–C1 分级词库，本地离线',
        '悬停看中文，右侧小球切换等级',
        '不收集数据，设置仅存本地',
    ):
        draw.ellipse((48, y + 9, 60, y + 21), fill=ACCENT)
        for i, line in enumerate(wrap_text(draw, bullet, load_font(18), text_right - 72)):
            draw.text((72, y + i * 26), line, fill=TEXT, font=load_font(18))
        y += 26 * max(1, len(wrap_text(draw, bullet, load_font(18), text_right - 72))) + 12

    draw.line([(48, h - 42), (220, h - 42)], fill=RING, width=4)
    draw.text((48, h - 34), 'github.com/code-corey/EnglishViewLearner', fill=RING, font=load_font(16))
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    export_screenshots()

    small_path = OUT / 'promo-tile-440x280.png'
    make_small_tile().save(small_path, format='PNG')
    print(f'Wrote {small_path}')

    marquee_path = OUT / 'promo-marquee-1400x560.png'
    make_marquee().save(marquee_path, format='PNG')
    print(f'Wrote {marquee_path}')


if __name__ == '__main__':
    main()
