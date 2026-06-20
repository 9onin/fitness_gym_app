from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from html import escape
import re
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EMU_PER_INCH = 914400


def xml_text(text):
    return escape(text, quote=False)


def paragraph(text="", style=None, align=None, bold=False):
    ppr = []
    ppr.append('<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>')
    if not style:
        ppr.append('<w:ind w:firstLine="709"/>')
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    if not text:
        return f"<w:p>{ppr_xml}</w:p>"
    return f"<w:p>{ppr_xml}<w:r>{rpr}<w:t xml:space=\"preserve\">{xml_text(text)}</w:t></w:r></w:p>"


def table_paragraph(text="", bold=False):
    rpr = (
        '<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
        '<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
        if bold
        else '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
        '<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
    )
    ppr = '<w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
    return f'<w:p>{ppr}<w:r>{rpr}<w:t xml:space="preserve">{xml_text(str(text))}</w:t></w:r></w:p>'


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table_xml(headers, rows):
    table_width = 9638
    col_count = max(1, len(headers))
    col_width = table_width // col_count

    def cell(text, header=False):
        shade = '<w:shd w:fill="D9EAF7"/>' if header else ""
        bold = header
        return (
            "<w:tc><w:tcPr>"
            f'<w:tcW w:w="{col_width}" w:type="dxa"/>'
            '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
            '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tcMar>'
            f"{shade}</w:tcPr>"
            f"{table_paragraph(str(text), bold=bold)}"
            "</w:tc>"
        )

    xml = [
        "<w:tbl>",
        "<w:tblPr>",
        f'<w:tblW w:w="{table_width}" w:type="dxa"/>',
        '<w:tblLayout w:type="fixed"/>',
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tblBorders>',
        "</w:tblPr>",
        "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{col_width}"/>' for _ in range(col_count)) + "</w:tblGrid>",
        "<w:tr>" + "".join(cell(h, True) for h in headers) + "</w:tr>",
    ]
    for row in rows:
        xml.append("<w:tr>" + "".join(cell(c) for c in row) + "</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def image_xml(rel_id, image_id, width_px, height_px, caption):
    max_width_inches = 6.1
    width_inches = min(max_width_inches, width_px / 160)
    height_inches = width_inches * height_px / max(width_px, 1)
    if height_inches > 7.0:
        height_inches = 7.0
        width_inches = height_inches * width_px / max(height_px, 1)
    cx = int(width_inches * EMU_PER_INCH)
    cy = int(height_inches * EMU_PER_INCH)
    return f"""
<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>
<wp:inline distT="0" distB="0" distL="0" distR="0"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
<wp:extent cx="{cx}" cy="{cy}"/>
<wp:docPr id="{image_id}" name="{xml_text(caption)}"/>
<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:nvPicPr><pic:cNvPr id="{image_id}" name="{xml_text(caption)}"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rel_id}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
</pic:pic></a:graphicData></a:graphic>
</wp:inline></w:drawing></w:r></w:p>
"""


def is_major_heading(line):
    return line in {
        "ВЫПУСКНАЯ КВАЛИФИКАЦИОННАЯ РАБОТА",
        "СОДЕРЖАНИЕ",
        "СПИСОК СОКРАЩЕНИЙ",
        "ВВЕДЕНИЕ",
        "ГЛАВА 1. АНАЛИТИЧЕСКАЯ ЧАСТЬ",
        "ГЛАВА 2. ПРАКТИЧЕСКАЯ ЧАСТЬ",
        "ЗАКЛЮЧЕНИЕ",
        "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        "ПРИЛОЖЕНИЯ",
        "ДОКУМЕНТАЦИЯ ДЛЯ РАССКАЗА НА ЗАЩИТЕ",
    }


def is_subheading(line):
    return bool(re.match(r"^\d+\.\d+\. ", line)) or line in {
        "КРАТКИЙ ДОКЛАД НА 7-10 МИНУТ",
        "СТРУКТУРА ПРЕЗЕНТАЦИИ",
        "КОРОТКИЕ ОТВЕТЫ НА ВОЗМОЖНЫЕ ВОПРОСЫ",
        "ТЕКСТ ДЛЯ ЗАВЕРШЕНИЯ ЗАЩИТЫ",
    }


def split_table_title(line):
    match = re.match(r"^(Таблица\s+\d+)\s+-\s+(.+)$", line)
    if match:
        return match.group(1), match.group(2)
    return line, ""


def build_document_xml(text, relationships, media_files):
    lines = text.splitlines()
    body = []
    i = 0
    image_counter = 1
    started = False

    while i < len(lines):
        raw = lines[i].rstrip()
        line = raw.strip()

        if not line:
            i += 1
            continue

        if line.startswith("[[IMAGE:") and line.endswith("]]"):
            payload = line[len("[[IMAGE:"):-2]
            image_rel, caption = payload.split("|", 1)
            image_path = ROOT / image_rel
            ext = image_path.suffix.lower().lstrip(".")
            rel_id = f"rId{len(relationships) + 1}"
            target = f"media/image{image_counter}.{ext}"
            relationships.append((rel_id, target, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"))
            media_files.append((image_path, f"word/{target}"))
            with Image.open(image_path) as im:
                width_px, height_px = im.size
            body.append(image_xml(rel_id, image_counter, width_px, height_px, caption))
            body.append(paragraph(caption, align="center"))
            image_counter += 1
            i += 1
            continue

        if line.startswith("Таблица ") and i + 2 < len(lines) and "|" in lines[i + 1] and set(lines[i + 2].replace("|", "").replace(" ", "")) <= {"-"}:
            table_num, table_name = split_table_title(line)
            body.append(paragraph(table_num, align="right", bold=True))
            if table_name:
                body.append(paragraph(table_name, align="center", bold=True))
            headers = [h.strip() for h in lines[i + 1].split("|")]
            i += 3
            rows = []
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                rows.append([c.strip() for c in lines[i].split("|")])
                i += 1
            body.append(table_xml(headers, rows))
            continue

        if is_major_heading(line):
            if started and line not in {"СОДЕРЖАНИЕ"}:
                body.append(page_break())
            body.append(paragraph(line, style="Heading1", align="center", bold=True))
            started = True
        elif is_subheading(line):
            body.append(paragraph(line, style="Heading2", align="center", bold=True))
        else:
            body.append(paragraph(line))
        i += 1

    sect = (
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:footerReference w:type="default" r:id="rIdFooter1"/>'
        '<w:pgMar w:top="1134" w:right="567" w:bottom="1134" w:left="1701" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
<w:body>{''.join(body)}{sect}</w:body></w:document>"""


def styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal">
<w:name w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="709"/><w:jc w:val="both"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading1">
<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="240" w:after="240"/><w:jc w:val="center"/></w:pPr>
<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="28"/></w:rPr>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading2">
<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="180" w:after="180"/><w:jc w:val="center"/></w:pPr>
<w:rPr><w:b/><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="28"/></w:rPr>
</w:style>
</w:styles>"""


def content_types(media_files):
    defaults = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        '<Default Extension="jpg" ContentType="image/jpeg"/>',
        '<Default Extension="jpeg" ContentType="image/jpeg"/>',
    ]
    overrides = [
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>',
    ]
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{''.join(defaults)}{''.join(overrides)}</Types>"""


def root_rels():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def doc_rels(relationships):
    rels = [
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
        '<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>',
    ]
    rels.extend(
        f'<Relationship Id="{rid}" Type="{rtype}" Target="{target}"/>'
        for rid, target, rtype in relationships
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


def footer_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p>
<w:pPr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>1</w:t></w:r>
<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>
</w:p>
</w:ftr>"""


def create_docx(txt_path, docx_path):
    text = Path(txt_path).read_text(encoding="utf-8")
    relationships = []
    media_files = []
    document = build_document_xml(text, relationships, media_files)
    with ZipFile(docx_path, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(media_files))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/footer1.xml", footer_xml())
        z.writestr("word/_rels/document.xml.rels", doc_rels(relationships))
        for source, arcname in media_files:
            z.write(source, arcname)
    print(docx_path)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: create_docx_from_text.py input.txt output.docx")
    create_docx(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
