import sys
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TXT_PATH = ROOT / "docs" / "diploma_text_format_fitness_gym.txt"
PDF_PATH = ROOT / "docs" / "diploma_text_format_fitness_gym.pdf"
FONT_PATH = ROOT / "timesnewromanpsmt.ttf"


DPI = 150
PAGE_W = int(8.27 * DPI)
PAGE_H = int(11.69 * DPI)
MARGIN_LEFT = int(0.9 * DPI)
MARGIN_RIGHT = int(0.65 * DPI)
MARGIN_TOP = int(0.75 * DPI)
MARGIN_BOTTOM = int(0.75 * DPI)

BODY_SIZE = 31
HEADING_SIZE = 34
TITLE_SIZE = 37
LINE_GAP = 11
PARA_GAP = 14


def font(size):
    return ImageFont.truetype(str(FONT_PATH), size)


BODY_FONT = font(BODY_SIZE)
HEADING_FONT = font(HEADING_SIZE)
TITLE_FONT = font(TITLE_SIZE)


def new_page():
    image = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    return image, ImageDraw.Draw(image), MARGIN_TOP


def is_heading(line):
    stripped = line.strip()
    if not stripped:
        return False
    return (
        stripped in {
            "ВВЕДЕНИЕ",
            "ЗАКЛЮЧЕНИЕ",
            "СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ",
            "ПРИЛОЖЕНИЯ",
        }
        or stripped.startswith("ГЛАВА ")
        or stripped.startswith("ШАБЛОН ДОКЛАДА")
        or stripped.startswith("ПАМЯТКА ")
        or stripped.startswith("РЕКОМЕНДУЕМАЯ ")
        or stripped.startswith("СПИСОК СОКРАЩЕНИЙ")
    )


def wrap_line(draw, text, selected_font, max_width):
    if not text:
        return [""]

    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if draw.textlength(candidate, font=selected_font) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = word
        else:
            parts = textwrap.wrap(word, width=35) or [word]
            lines.extend(parts[:-1])
            current = parts[-1]

    if current:
        lines.append(current)
    return lines


def render(txt_path=TXT_PATH, pdf_path=PDF_PATH):
    text = Path(txt_path).read_text(encoding="utf-8")
    max_width = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT
    pages = []
    page, draw, y = new_page()

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("[[IMAGE:") and line.endswith("]]"):
            payload = line[len("[[IMAGE:"):-2]
            image_rel, caption = payload.split("|", 1)
            image_path = ROOT / image_rel
            figure = Image.open(image_path).convert("RGB")
            max_img_width = max_width
            max_img_height = int((PAGE_H - MARGIN_TOP - MARGIN_BOTTOM) * 0.56)
            scale = min(max_img_width / figure.width, max_img_height / figure.height, 1.0)
            new_size = (int(figure.width * scale), int(figure.height * scale))
            figure = figure.resize(new_size, Image.LANCZOS)
            caption_lines = wrap_line(draw, caption, BODY_FONT, max_width)
            caption_height = len(caption_lines) * (BODY_SIZE + LINE_GAP) + PARA_GAP
            block_height = figure.height + caption_height + PARA_GAP

            if y + block_height > PAGE_H - MARGIN_BOTTOM:
                pages.append(page)
                page, draw, y = new_page()

            x = int((PAGE_W - figure.width) / 2)
            page.paste(figure, (x, y))
            y += figure.height + PARA_GAP
            for part in caption_lines:
                x_text = (PAGE_W - draw.textlength(part, font=BODY_FONT)) / 2
                draw.text((x_text, y), part, font=BODY_FONT, fill="black")
                y += BODY_SIZE + LINE_GAP
            y += PARA_GAP
            continue

        if not line:
            y += PARA_GAP
            continue

        selected_font = HEADING_FONT if is_heading(line) else BODY_FONT
        if line.startswith("ВЫПУСКНАЯ"):
            selected_font = TITLE_FONT

        wrapped = wrap_line(draw, line, selected_font, max_width)
        line_height = selected_font.getbbox("АБВабв")[3] - selected_font.getbbox("АБВабв")[1] + LINE_GAP
        block_height = len(wrapped) * line_height + PARA_GAP

        if y + block_height > PAGE_H - MARGIN_BOTTOM:
            pages.append(page)
            page, draw, y = new_page()

        for part in wrapped:
            if is_heading(line) or line.startswith("ВЫПУСКНАЯ"):
                x = (PAGE_W - draw.textlength(part, font=selected_font)) / 2
            else:
                x = MARGIN_LEFT
            draw.text((x, y), part, font=selected_font, fill="black")
            y += line_height
        y += PARA_GAP

    pages.append(page)
    pages[0].save(pdf_path, "PDF", resolution=DPI, save_all=True, append_images=pages[1:])
    print(f"{pdf_path} ({len(pages)} pages)")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        render(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        render()
