import os
import string
import sys

from PIL import Image, ImageDraw, ImageFont

GRID = 64
MARGIN_LEFT = GRID
MARGIN_BOTTOM = GRID


def _col_label(i):
    label = ""
    while True:
        label = string.ascii_uppercase[i % 26] + label
        i = i // 26 - 1
        if i < 0:
            break
    return label


def generate_grid(input_path):
    """Overlay a labeled 64px grid on the image at input_path. Returns the output path."""
    img = Image.open(input_path)
    w, h = img.size

    cols = w // GRID
    rows = h // GRID

    new_w = MARGIN_LEFT + cols * GRID
    new_h = rows * GRID + MARGIN_BOTTOM

    canvas = Image.new("RGB", (new_w, new_h), "white")
    canvas.paste(img.crop((0, 0, cols * GRID, rows * GRID)), (MARGIN_LEFT, 0))

    draw = ImageDraw.Draw(canvas)

    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Roboto-Regular.ttf")
    font = ImageFont.truetype(font_path, 44)

    for c in range(cols + 1):
        x = MARGIN_LEFT + c * GRID
        draw.line([(x, 0), (x, rows * GRID)], fill=(255, 0, 0, 128), width=1)

    for r in range(rows + 1):
        y = r * GRID
        draw.line([(MARGIN_LEFT, y), (new_w, y)], fill=(255, 0, 0, 128), width=1)

    for c in range(cols):
        lbl = _col_label(c)
        cell_x = MARGIN_LEFT + c * GRID
        cell_y = rows * GRID
        bbox = draw.textbbox((0, 0), lbl, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cell_x + (GRID - tw) // 2, cell_y + (GRID - th) // 2), lbl, fill="black", font=font)

    # 1-digit row numbers are centered as if they were "0N" (aligned with 2-digit numbers)
    ref_bbox = draw.textbbox((0, 0), "00", font=font)
    ref_tw = ref_bbox[2] - ref_bbox[0]
    for r in range(rows):
        lbl = str(r + 1)
        cell_y = r * GRID
        bbox = draw.textbbox((0, 0), lbl, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if len(lbl) == 1:
            zero_bbox = draw.textbbox((0, 0), "0", font=font)
            zero_w = zero_bbox[2] - zero_bbox[0]
            x = (MARGIN_LEFT - ref_tw) // 2 + zero_w
        else:
            x = (MARGIN_LEFT - tw) // 2
        y = cell_y + (GRID - th) // 2
        draw.text((x, y), lbl, fill="black", font=font)

    output_path = os.path.splitext(input_path)[0] + "_grid.png"
    canvas.save(output_path)
    return output_path, new_w, new_h, cols, rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: grid.py <screenshot-path>")
    in_path = sys.argv[1]
    out_path, w, h, cols, rows = generate_grid(in_path)
    print(f"Saved {out_path} ({w}x{h}), {cols} cols x {rows} rows")
