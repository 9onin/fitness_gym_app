from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}

ET.register_namespace("w", W)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing")
ET.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
ET.register_namespace("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture")


def qn(name):
    return f"{{{W}}}{name}"


def has_text(run):
    return run.find(".//w:t", NS) is not None or run.find(".//w:instrText", NS) is not None


def blacken_xml(data):
    root = ET.fromstring(data)
    changed = False

    for run in root.findall(".//w:r", NS):
        if not has_text(run):
            continue
        rpr = run.find("w:rPr", NS)
        if rpr is None:
            rpr = ET.Element(qn("rPr"))
            run.insert(0, rpr)
            changed = True
        color = rpr.find("w:color", NS)
        if color is None:
            color = ET.SubElement(rpr, qn("color"))
            changed = True
        for attr in list(color.attrib):
            if attr.endswith("themeColor") or attr.endswith("themeShade") or attr.endswith("themeTint"):
                del color.attrib[attr]
                changed = True
        if color.get(qn("val")) != "000000":
            color.set(qn("val"), "000000")
            changed = True

    for style_color in root.findall(".//w:color", NS):
        for attr in list(style_color.attrib):
            if attr.endswith("themeColor") or attr.endswith("themeShade") or attr.endswith("themeTint"):
                del style_color.attrib[attr]
                changed = True
        if style_color.get(qn("val")) != "000000":
            style_color.set(qn("val"), "000000")
            changed = True

    if not changed:
        return data
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def process_docx(path):
    path = Path(path)
    with ZipFile(path, "r") as zin:
        with NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp_path = Path(tmp.name)
        with ZipFile(tmp_path, "w", ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                    try:
                        data = blacken_xml(data)
                    except ET.ParseError:
                        pass
                zout.writestr(item, data)
    tmp_path.replace(path)
    print(path)


def main():
    if len(__import__("sys").argv) < 2:
        raise SystemExit("Usage: force_docx_text_black.py file.docx [file2.docx ...]")
    for arg in __import__("sys").argv[1:]:
        process_docx(arg)


if __name__ == "__main__":
    main()
