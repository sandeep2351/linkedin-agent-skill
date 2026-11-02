"""Draw a tall infographic and turn it into a short GIF.

The GIF walks down the stages. It is the image you attach to the LinkedIn post.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
MARGIN = 36
RAIL = 176

PAPER = (244, 236, 216)
INK = (22, 26, 22)
GREEN = (27, 107, 52)
GREEN_DARK = (12, 74, 44)
BAND = (226, 239, 214)
CARD = (255, 252, 246)
PILL = (232, 244, 220)
RED = (176, 42, 42)
WHITE = (255, 255, 255)

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    """Break a sentence so it stays inside the card."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _icon(draw: ImageDraw.ImageDraw, kind: str, box: tuple[int, int, int, int]) -> None:
    """A small white mark inside the green circle. One shape per stage."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    if kind == "flask":
        draw.polygon([(cx, cy - 28), (cx - 18, cy + 22), (cx + 18, cy + 22)], outline=WHITE, width=4)
        draw.line([(cx, cy - 28), (cx, cy - 40)], fill=WHITE, width=4)
    elif kind == "data":
        draw.ellipse((cx - 26, cy - 34, cx + 26, cy - 16), outline=WHITE, width=4)
        draw.line([(cx - 26, cy - 24), (cx - 26, cy + 16)], fill=WHITE, width=4)
        draw.line([(cx + 26, cy - 24), (cx + 26, cy + 16)], fill=WHITE, width=4)
        draw.arc((cx - 26, cy + 4, cx + 26, cy + 30), 0, 180, fill=WHITE, width=4)
    elif kind == "nodes":
        for dx, dy in ((-22, 8), (22, 8), (0, -22)):
            draw.ellipse((cx + dx - 8, cy + dy - 8, cx + dx + 8, cy + dy + 8), outline=WHITE, width=4)
        draw.line([(cx - 14, cy + 8), (cx, cy - 14)], fill=WHITE, width=3)
        draw.line([(cx + 14, cy + 8), (cx, cy - 14)], fill=WHITE, width=3)
    elif kind == "check":
        draw.line([(cx - 20, cy), (cx - 6, cy + 16), (cx + 22, cy - 18)], fill=WHITE, width=5)
    else:
        draw.polygon([(cx - 8, cy + 24), (cx - 8, cy - 8), (cx - 22, cy - 8), (cx, cy - 32), (cx + 22, cy - 8), (cx + 8, cy - 8), (cx + 8, cy + 24)], fill=WHITE)


def render_board(board: dict, highlight: int | None = None) -> Image.Image:
    """Paint one frame. `highlight` is the stage index that should read as the current step."""
    title_font = _font(FONT_BOLD, 54)
    name_font = _font(FONT_BOLD, 22)
    stage_font = _font(FONT_BOLD, 26)
    head_font = _font(FONT_BOLD, 30)
    body_font = _font(FONT_REG, 24)
    pill_font = _font(FONT_BOLD, 20)
    measure = ImageDraw.Draw(Image.new("RGB", (WIDTH, 100), PAPER))

    # Measure the title and every stage before allocating the canvas.
    title_lines = []
    for raw in board["title"].split("\n"):
        title_lines.extend(_wrap(measure, raw, title_font, WIDTH - MARGIN * 2))
    stage_heights = []
    text_width = WIDTH - MARGIN * 2 - RAIL - 48
    for stage in board["stages"]:
        lines = []
        for point in stage["points"]:
            lines.extend(_wrap(measure, point, body_font, text_width - 28))
        callout = stage.get("callout") or ""
        callout_lines = _wrap(measure, callout, body_font, text_width - 36) if callout else []
        pills = stage.get("tools") or []
        height = 28 + 40 + len(lines) * 32 + (16 + len(callout_lines) * 30 + 20 if callout_lines else 0)
        height += 18 + 36 if pills else 8
        stage_heights.append(max(height, 168))

    header = 36 + 28 + 16 + len(title_lines) * 62 + 18
    height = header + sum(stage_heights) + 24 * len(stage_heights) + 70
    image = Image.new("RGB", (WIDTH, height), PAPER)
    draw = ImageDraw.Draw(image)

    # Name line, then the roadmap title.
    draw.text((MARGIN, 28), "P. Sandeep Kalyan   ·   DevOps  ·  Cloud  ·  AI", font=name_font, fill=GREEN_DARK)
    y = 72
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += 62
    y += 8

    icons = ["flask", "data", "nodes", "check", "rocket"]
    for index, stage in enumerate(board["stages"]):
        block_h = stage_heights[index]
        top = y
        # The active stage gets a darker edge so the GIF has a place to rest the eye.
        edge = GREEN_DARK if highlight == index else BAND
        draw.rounded_rectangle((MARGIN, top, WIDTH - MARGIN, top + block_h), radius=22, fill=BAND, outline=edge, width=6 if highlight == index else 1)
        draw.rounded_rectangle((MARGIN + 16, top + 16, MARGIN + RAIL - 8, top + block_h - 16), radius=18, fill=GREEN_DARK)
        circle = (MARGIN + 46, top + 28, MARGIN + RAIL - 42, top + 112)
        draw.ellipse(circle, outline=WHITE, width=3)
        _icon(draw, icons[index % len(icons)], circle)
        # The stage name sits under the icon, so a tall card does not leave a floating label.
        label = _wrap(draw, stage["name"], stage_font, RAIL - 36)
        label_y = top + 122
        for line in label:
            tw = draw.textlength(line, font=stage_font)
            draw.text((MARGIN + 16 + (RAIL - 24 - tw) / 2, label_y), line, font=stage_font, fill=WHITE)
            label_y += 30

        content_x = MARGIN + RAIL + 8
        draw.rounded_rectangle((content_x, top + 16, WIDTH - MARGIN - 16, top + block_h - 16), radius=16, fill=CARD)
        cursor = top + 28
        draw.text((content_x + 20, cursor), f"{index + 1}   {stage['title']}", font=head_font, fill=INK)
        cursor += 46
        for point in stage["points"]:
            wrapped = _wrap(draw, point, body_font, text_width - 28)
            for line_index, line in enumerate(wrapped):
                prefix = "→  " if line_index == 0 else "    "
                draw.text((content_x + 20, cursor), prefix + line, font=body_font, fill=INK)
                cursor += 32
        if stage.get("callout"):
            cursor += 8
            callout_lines = _wrap(draw, stage["callout"], body_font, text_width - 36)
            box_h = 16 + len(callout_lines) * 30
            draw.rounded_rectangle((content_x + 16, cursor, WIDTH - MARGIN - 32, cursor + box_h), radius=10, fill=(255, 236, 232), outline=RED, width=2)
            inner = cursor + 8
            for line in callout_lines:
                draw.text((content_x + 28, inner), line, font=body_font, fill=RED)
                inner += 30
            cursor += box_h + 8
        pill_x = content_x + 20
        pill_y = top + block_h - 52
        for tool in stage.get("tools") or []:
            tw = draw.textlength(tool, font=pill_font)
            if pill_x + tw + 28 > WIDTH - MARGIN - 32:
                break
            draw.rounded_rectangle((pill_x, pill_y, pill_x + tw + 22, pill_y + 32), radius=14, fill=PILL, outline=GREEN, width=2)
            draw.text((pill_x + 11, pill_y + 4), tool, font=pill_font, fill=GREEN_DARK)
            pill_x += tw + 32
        y += block_h + 18

    draw.text((MARGIN, height - 48), "Save this roadmap.   Production is the next 10,000 responses.", font=name_font, fill=GREEN_DARK)
    return image


def write_gif(board: dict, gif_path: Path, preview_path: Path) -> None:
    """Write a preview PNG and a GIF that highlights one stage at a time."""
    frames = [render_board(board, highlight=index) for index in range(len(board["stages"]))]
    frames.append(render_board(board, highlight=None))
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    frames[-1].save(preview_path, format="PNG", optimize=True)
    # One palette keeps the animation from flickering between frames.
    palette = frames[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    quantized = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [1100] * len(board["stages"]) + [1800]
    quantized[0].save(
        gif_path,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
