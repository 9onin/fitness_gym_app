from copy import deepcopy
from html import escape
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TEMPLATE = sorted((Path.home() / "Downloads").glob("*ВКР-1.docx"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
SOURCE_DOCX = DOCS / "diploma_full_fitness_gym.docx"
OUT = DOCS / "Черников_Никита_Александрович_ВКР.docx"
ZIP_OUT = DOCS / "Черников_Никита_Александрович_ВКР.zip"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W}
ET.register_namespace("w", W)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing")
ET.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
ET.register_namespace("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture")

FULL_NAME = "Черников Никита Александрович"
SHORT_NAME = "Черников Н. А."
OLD_FULL_NAME = "\u0414\u0435\u043c\u0438\u0434\u043e\u0432 \u0414\u043c\u0438\u0442\u0440\u0438\u0439 \u0412\u044f\u0447\u0435\u0441\u043b\u0430\u0432\u043e\u0432\u0438\u0447"
OLD_SHORT_NAME = "\u0414\u0435\u043c\u0438\u0434\u043e\u0432 \u0414. \u0412."
OLD_TOPIC = "\u0420\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430 \u0438 \u043e\u043f\u0442\u0438\u043c\u0438\u0437\u0430\u0446\u0438\u044f \u0432\u044b\u0441\u043e\u043a\u043e\u043d\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043d\u043e\u0433\u043e \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0434\u043b\u044f \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0438 \u0438 \u043f\u043e\u0442\u043e\u043a\u043e\u0432\u043e\u0439 \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0438 \u043c\u0435\u0434\u0438\u0430\u043a\u043e\u043d\u0442\u0435\u043d\u0442\u0430 \u0432 \u041e\u0421 Linux"
OLD_TOPIC_LINE_1 = "\u0420\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430 \u0438 \u043e\u043f\u0442\u0438\u043c\u0438\u0437\u0430\u0446\u0438\u044f \u0432\u044b\u0441\u043e\u043a\u043e\u043d\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043d\u043e\u0433\u043e \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f \u0434\u043b\u044f"
OLD_TOPIC_LINE_2 = "\u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0438 \u0438 \u043f\u043e\u0442\u043e\u043a\u043e\u0432\u043e\u0439 \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0438 \u043c\u0435\u0434\u0438\u0430\u043a\u043e\u043d\u0442\u0435\u043d\u0442\u0430 \u0432 \u041e\u0421 Linux"
OLD_OUR_TOPIC = "Разработка и тестирование информационной системы для управления фитнес-клубом"
TOPIC = "Откладка и тестирование информационной системы для учета клиентов фитнес-клуба с интеграцией мобильных приложений"
TOPIC_LINE_1 = "Откладка и тестирование информационной системы для учета клиентов"
TOPIC_LINE_2 = "фитнес-клуба с интеграцией мобильных приложений"


def qn(name):
    return f"{{{W}}}{name}"


def paragraph_text(p):
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def set_paragraph_text(p, text):
    first_run = p.find("./w:r", NS)
    rpr = deepcopy(first_run.find("./w:rPr", NS)) if first_run is not None and first_run.find("./w:rPr", NS) is not None else None
    for child in list(p):
        if child.tag != qn("pPr"):
            p.remove(child)
    run = ET.SubElement(p, qn("r"))
    if rpr is not None:
        run.append(rpr)
    t = ET.SubElement(run, qn("t"))
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text


def replace_in_runs(p, old, new):
    for t in p.findall(".//w:t", NS):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new)


def patch_front_paragraph(p):
    text = paragraph_text(p).strip()
    if not text:
        return
    assignment_replacements = {
        "2. Аналитическая часть:": (
            "2. Аналитическая часть: характеристика предметной области фитнес-клуба; анализ проблем "
            "ручного учета клиентов, расписания, абонементов и посещаемости; обзор аналогичных цифровых "
            "решений; формирование функциональных и нефункциональных требований; обоснование выбора "
            "архитектуры, языка программирования, фреймворка и средств хранения данных."
        ),
        "3. Практическая часть:": (
            "3. Практическая часть: проектирование структуры Flask-приложения и базы данных; разработка "
            "пользовательских функций регистрации, авторизации, просмотра расписания, записи на тренировки "
            "и работы с абонементами; разработка административной панели для управления клиентами, "
            "тренерами, тренировками, тарифами и отчетностью; построение диаграмм, таблиц и пользовательских "
            "сценариев; проведение отладки и тестирования основных функций системы."
        ),
        "6. Приложения:": (
            "6. Приложения: диаграммы архитектуры приложения, ER-диаграмма базы данных, диаграмма классов "
            "моделей, диаграмма прецедентов, схема тестирования, скриншоты главной страницы, интерфейса "
            "посетителя и административной панели, фрагменты программной и пользовательской документации."
        ),
    }
    if text in assignment_replacements:
        set_paragraph_text(p, assignment_replacements[text])
        return
    if text == OLD_FULL_NAME:
        set_paragraph_text(p, FULL_NAME)
    elif text == OLD_SHORT_NAME:
        set_paragraph_text(p, SHORT_NAME)
    elif text in {OLD_TOPIC, f"«{OLD_TOPIC}»"}:
        set_paragraph_text(p, f"«{TOPIC}»" if text.startswith("«") else TOPIC)
    elif text == OLD_TOPIC_LINE_1:
        set_paragraph_text(p, TOPIC_LINE_1)
    elif text == OLD_TOPIC_LINE_2:
        set_paragraph_text(p, TOPIC_LINE_2)
    elif text.startswith("Тема:") and OLD_TOPIC in text:
        set_paragraph_text(p, f"Тема: «{TOPIC}»")
    else:
        replace_in_runs(p, OLD_FULL_NAME, FULL_NAME)
        replace_in_runs(p, OLD_SHORT_NAME, SHORT_NAME)
        replace_in_runs(p, OLD_TOPIC, TOPIC)


def patch_body_paragraph(p):
    text = paragraph_text(p)
    if OLD_OUR_TOPIC in text:
        set_paragraph_text(p, text.replace(OLD_OUR_TOPIC, TOPIC))


def find_body_start(children, marker):
    for idx, child in enumerate(children):
        if child.tag == qn("p") and paragraph_text(child).strip() == marker:
            return idx
    raise RuntimeError(f"Marker not found: {marker}")


def max_rid(rels_root):
    max_id = 0
    for rel in rels_root:
        rid = rel.get("Id", "")
        if rid.startswith("rId") and rid[3:].isdigit():
            max_id = max(max_id, int(rid[3:]))
    return max_id


def replace_blip_ids(element, rid_map):
    embed_attr = f"{{{R}}}embed"
    link_attr = f"{{{R}}}link"
    for node in element.iter():
        if embed_attr in node.attrib and node.attrib[embed_attr] in rid_map:
            node.attrib[embed_attr] = rid_map[node.attrib[embed_attr]]
        if link_attr in node.attrib and node.attrib[link_attr] in rid_map:
            node.attrib[link_attr] = rid_map[node.attrib[link_attr]]


def serialize_rels(rels_root):
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        f'<Relationships xmlns="{REL}">',
    ]
    for rel in rels_root:
        attrs = []
        for key in ("Id", "Type", "Target", "TargetMode"):
            value = rel.get(key)
            if value is not None:
                attrs.append(f'{key}="{escape(value, quote=True)}"')
        lines.append(f'<Relationship {" ".join(attrs)}/>')
    lines.append("</Relationships>")
    return "\n".join(lines).encode("utf-8")


TOC_LINES = [
    "СПИСОК СОКРАЩЕНИЙ4",
    "ВВЕДЕНИЕ6",
    "ГЛАВА 1. АНАЛИТИЧЕСКАЯ ЧАСТЬ10",
    "1.1. Характеристика предметной области фитнес-клуба10",
    "1.2. Анализ проблем действующей организации учета12",
    "1.3. Обзор цифровых решений для фитнес-индустрии14",
    "1.4. Формирование требований к информационной системе17",
    "1.5. Выбор архитектуры и технологического стека19",
    "1.6. Выводы по первой главе29",
    "ГЛАВА 2. ПРАКТИЧЕСКАЯ ЧАСТЬ31",
    "2.1. Общая характеристика разработанной информационной системы31",
    "2.2. Проектирование структуры проекта и архитектуры приложения34",
    "2.3. Проектирование базы данных39",
    "2.4. Реализация пользовательских функций44",
    "2.5. Реализация административных функций47",
    "2.6. Реализация абонементов, уведомлений и отчетности51",
    "2.7. Тестирование и отладка системы54",
    "2.8. Оценка результата внедрения58",
    "2.9. Выводы по второй главе61",
    "ЗАКЛЮЧЕНИЕ63",
    "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ66",
    "ПРИЛОЖЕНИЯ70",
    "Приложение А70",
    "Приложение Б75",
    "Приложение В83",
    "Приложение Г103",
]


def patch_template_toc(children, toc_idx, body_start_idx):
    repl_idx = 0
    for child in children[toc_idx + 1:body_start_idx]:
        if child.tag != qn("p"):
            continue
        text = paragraph_text(child).strip()
        if not text:
            continue
        if repl_idx < len(TOC_LINES):
            set_paragraph_text(child, TOC_LINES[repl_idx])
            repl_idx += 1
        else:
            set_paragraph_text(child, "")


def build():
    with ZipFile(TEMPLATE) as z:
        template_doc = ET.fromstring(z.read("word/document.xml"))
        template_rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    with ZipFile(SOURCE_DOCX) as z:
        source_doc = ET.fromstring(z.read("word/document.xml"))
        source_rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))

    template_body = template_doc.find("w:body", NS)
    source_body = source_doc.find("w:body", NS)
    template_children = list(template_body)
    source_children = list(source_body)

    template_toc_idx = find_body_start(template_children, "СОДЕРЖАНИЕ")
    template_body_idx = find_body_start(template_children, "СПИСОК СОКРАЩЕНИЙ")
    source_toc_idx = find_body_start(source_children, "СОДЕРЖАНИЕ")
    source_body_idx = find_body_start(source_children, "СПИСОК СОКРАЩЕНИЙ")

    source_sect = source_body.find("w:sectPr", NS)
    template_sect = template_body.find("w:sectPr", NS)

    source_image_rels = {}
    for rel in source_rels:
        if rel.get("Type", "").endswith("/image"):
            source_image_rels[rel.get("Id")] = rel.get("Target")

    rid_map = {}
    media_to_copy = []
    next_rid = max_rid(template_rels) + 1
    next_image = 100
    for old_rid, old_target in source_image_rels.items():
        new_rid = f"rId{next_rid}"
        next_rid += 1
        ext = Path(old_target).suffix or ".png"
        new_target = f"media/chernikov_image{next_image}{ext}"
        next_image += 1
        rid_map[old_rid] = new_rid
        rel = ET.Element(f"{{{REL}}}Relationship")
        rel.set("Id", new_rid)
        rel.set("Type", f"{R}/image")
        rel.set("Target", new_target)
        template_rels.append(rel)
        media_to_copy.append((old_target, new_target))

    source_content = []
    for child in source_children[source_body_idx:]:
        if child.tag != qn("sectPr"):
            copied = deepcopy(child)
            replace_blip_ids(copied, rid_map)
            if copied.tag == qn("p"):
                patch_body_paragraph(copied)
            source_content.append(copied)

    front = []
    template_front_children = [deepcopy(child) for child in template_children[:template_body_idx]]
    patch_template_toc(template_front_children, template_toc_idx, template_body_idx)
    for child in template_front_children:
        copied = deepcopy(child)
        if copied.tag == qn("p"):
            patch_front_paragraph(copied)
        front.append(copied)

    new_body = template_doc.find("w:body", NS)
    for child in list(new_body):
        new_body.remove(child)
    for child in front + source_content:
        new_body.append(child)
    new_body.append(deepcopy(template_sect if template_sect is not None else source_sect))

    document_text = ET.tostring(template_doc, encoding="unicode", xml_declaration=True)
    document_text = document_text.replace(OLD_FULL_NAME, FULL_NAME)
    document_text = document_text.replace(OLD_SHORT_NAME, SHORT_NAME)
    document_text = document_text.replace(OLD_TOPIC, TOPIC)
    document_text = document_text.replace(OLD_TOPIC_LINE_1, TOPIC_LINE_1)
    document_text = document_text.replace(OLD_TOPIC_LINE_2, TOPIC_LINE_2)
    document_xml = document_text.encode("utf-8")
    rels_xml = serialize_rels(template_rels)

    with ZipFile(TEMPLATE) as base, ZipFile(SOURCE_DOCX) as source_zip, ZipFile(OUT, "w", ZIP_DEFLATED) as zout:
        existing = set()
        for item in base.infolist():
            data = base.read(item.filename)
            if item.filename == "word/document.xml":
                data = document_xml
            elif item.filename == "word/_rels/document.xml.rels":
                data = rels_xml
            zout.writestr(item, data)
            existing.add(item.filename)
        for old_target, new_target in media_to_copy:
            data = source_zip.read("word/" + old_target)
            arcname = "word/" + new_target
            if arcname not in existing:
                zout.writestr(arcname, data)
                existing.add(arcname)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with ZipFile(ZIP_OUT, "w", ZIP_DEFLATED) as z:
        z.write(OUT, OUT.name)

    print(OUT)
    print(ZIP_OUT)


if __name__ == "__main__":
    build()
