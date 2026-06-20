from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from html import escape

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "fitness_gym_defense_presentation.pptx"

SLIDE_W = 12192000
SLIDE_H = 6858000
EMU = 914400


def x(v):
    return int(v * EMU)


def xml(text):
    return escape(text, quote=False)


def text_runs(text, size=2400, bold=False, color="111827"):
    b = '<a:b/>' if bold else ''
    return f'<a:r><a:rPr lang="ru-RU" sz="{size}" dirty="0">{b}<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{xml(text)}</a:t></a:r>'


def paragraph(text, level=0, size=2400, bold=False, color="111827"):
    if level is None:
        margin = 0
        bullet = '<a:buNone/>'
    else:
        margin = level * 420000
        bullet = '<a:buChar char="•"/>'
    return (
        f'<a:p><a:pPr marL="{margin}" indent="-180000">{bullet}</a:pPr>'
        f'{text_runs(text, size=size, bold=bold, color=color)}'
        '</a:p>'
    )


def solid_fill(color):
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def line_xml(color="D1D5DB", width=12700):
    return f'<a:ln w="{width}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>'


def rect_shape(shape_id, name, left, top, width, height, fill="FFFFFF", line="E5E7EB", radius=False):
    geom = "roundRect" if radius else "rect"
    return f"""
<p:sp>
<p:nvSpPr><p:cNvPr id="{shape_id}" name="{xml(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{solid_fill(fill)}{line_xml(line)}</p:spPr>
</p:sp>
"""


def textbox(shape_id, name, left, top, width, height, lines, title=False, fill=None, line=None, radius=False, color="111827", title_size=3300):
    body = []
    for item in lines:
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, None if title else 0
        body.append(paragraph(text, level=level, size=title_size if title else 2150, bold=title, color=color))
    fill_xml = solid_fill(fill) if fill else "<a:noFill/>"
    line_part = line_xml(line) if line else "<a:ln><a:noFill/></a:ln>"
    geom = "roundRect" if radius else "rect"
    return f"""
<p:sp>
<p:nvSpPr><p:cNvPr id="{shape_id}" name="{xml(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
<p:spPr><a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{fill_xml}{line_part}</p:spPr>
<p:txBody><a:bodyPr wrap="square" lIns="180000" tIns="120000" rIns="180000" bIns="120000"/><a:lstStyle/>{''.join(body)}</p:txBody>
</p:sp>
"""


def title_shape(text):
    return textbox(2, "Title", x(0.55), x(0.22), x(11.9), x(0.72), [text], title=True, color="FFFFFF")


def footer_shape(num):
    return textbox(99, "Footer", x(11.62), x(7.08), x(0.7), x(0.25), [str(num)], title=True, color="64748B")


def image_shape(shape_id, rel_id, name, left, top, width, height):
    return f"""
<p:pic>
<p:nvPicPr><p:cNvPr id="{shape_id}" name="{xml(name)}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
<p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
<p:spPr><a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>
"""


def scaled_image(path, max_w_in, max_h_in):
    with Image.open(path) as im:
        w, h = im.size
    scale = min(max_w_in / (w / 160), max_h_in / (h / 160), 1.0)
    return x((w / 160) * scale), x((h / 160) * scale)


def slide_xml(slide, idx):
    shapes = [
        rect_shape(100, "Background", 0, 0, SLIDE_W, SLIDE_H, fill="F8FAFC", line="F8FAFC"),
        rect_shape(101, "Header", 0, 0, SLIDE_W, x(1.05), fill="102A43", line="102A43"),
        rect_shape(102, "Accent", 0, x(1.05), x(0.18), x(6.45), fill="16A34A", line="16A34A"),
    ]
    if idx != 1:
        shapes.append(title_shape(slide["title"]))
    sid = 3
    if idx == 1:
        shapes.append(textbox(sid, "HeaderTitle", x(0.7), x(0.22), x(10.8), x(0.52), [
            "Выпускная квалификационная работа"
        ], title=True, color="FFFFFF", title_size=2350))
        sid += 1
        shapes.append(textbox(sid, "MainTitle", x(0.85), x(1.35), x(10.9), x(1.95), [
            "Отладка и тестирование информационной системы",
            "для учета клиентов фитнес-клуба",
            "с интеграцией мобильных приложений"
        ], title=True, fill="FFFFFF", line="E5E7EB", radius=True, color="102A43", title_size=2550))
        sid += 1
        cards = [
            ("Python + Flask", "серверная часть"),
            ("SQLite + SQLAlchemy", "база данных"),
            ("pytest", "проверка сценариев"),
        ]
        left = 0.85
        for label, sub in cards:
            shapes.append(textbox(sid, "Metric", x(left), x(3.75), x(3.55), x(1.05), [label, sub], title=False, fill="ECFDF5", line="BBF7D0", radius=True, color="064E3B"))
            sid += 1
            left += 3.85
        shapes.append(textbox(sid, "FooterNote", x(0.85), x(5.15), x(10.8), x(0.78), ["Специальность 09.02.07 Информационные системы и программирование"], title=True, fill="EFF6FF", line="BFDBFE", radius=True, color="1E3A8A", title_size=2200))
        shapes.append(footer_shape(idx))
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill></p:bgPr></p:bg>
<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{''.join(shapes)}</p:spTree></p:cSld>
<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""

    if "bullets" in slide:
        lines = []
        for b in slide["bullets"]:
            if isinstance(b, tuple):
                lines.append(b)
            else:
                lines.append((b, 0))
        shapes.append(textbox(sid, "Content", x(0.75), x(1.35), x(6.05 if slide.get("image") else 11.15), x(5.35), lines, fill="FFFFFF", line="E2E8F0", radius=True))
        sid += 1
    if slide.get("image"):
        rel_id = "rId2"
        img_w, img_h = scaled_image(ROOT / slide["image"], 5.2, 4.9)
        shapes.append(rect_shape(sid, "ImageFrame", x(7.0), x(1.32), x(5.35), x(5.25), fill="FFFFFF", line="CBD5E1", radius=True))
        sid += 1
        shapes.append(image_shape(sid, rel_id, slide["image"], x(7.08), x(1.48), img_w, img_h))
        sid += 1
    if slide.get("note"):
        shapes.append(textbox(sid, "Note", x(0.85), x(5.9), x(10.8), x(0.6), [slide["note"]], fill="FEF3C7", line="F59E0B", radius=True))
    shapes.append(footer_shape(idx))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg>
<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{''.join(shapes)}</p:spTree></p:cSld>
<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""


def slide_rels(has_image, idx):
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
    if has_image:
        rels.append(f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{idx}.png"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


def content_types(slide_count):
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
    ]
    overrides.extend(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
{''.join(overrides)}
</Types>"""


def root_rels():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""


def presentation_xml(slide_count):
    ids = "".join(f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in range(1, slide_count + 1))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{slide_count + 1}"/></p:sldMasterIdLst>
<p:sldIdLst>{ids}</p:sldIdLst>
<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
<p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def presentation_rels(slide_count):
    rels = [
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    ]
    rels.append(f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


def master_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>"""


def layout_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">
<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"""


def theme_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
<a:themeElements><a:clrScheme name="Office"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="16A34A"/></a:accent2><a:accent3><a:srgbClr val="F59E0B"/></a:accent3><a:accent4><a:srgbClr val="DC2626"/></a:accent4><a:accent5><a:srgbClr val="7C3AED"/></a:accent5><a:accent6><a:srgbClr val="0891B2"/></a:accent6><a:hlink><a:srgbClr val="0000FF"/></a:hlink><a:folHlink><a:srgbClr val="800080"/></a:folHlink></a:clrScheme><a:fontScheme name="Arial"><a:majorFont><a:latin typeface="Arial"/></a:majorFont><a:minorFont><a:latin typeface="Arial"/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>"""


SLIDES = [
    {"title": "Отладка и тестирование информационной системы для учета клиентов фитнес-клуба с интеграцией мобильных приложений", "bullets": ["Выпускная квалификационная работа", "Специальность 09.02.07 Информационные системы и программирование", "Проект: Fitness Gym App"]},
    {"title": "Актуальность", "bullets": ["Фитнес-клубу требуется единая цифровая среда", "Ручной учет повышает риск ошибок в расписании и абонементах", "Клиенту нужен самостоятельный доступ к тренировкам и записям", "Администрации нужны аналитика и централизованное управление"]},
    {"title": "Цель и задачи", "bullets": ["Цель: разработать и протестировать веб-систему управления фитнес-клубом", "Проанализировать предметную область", "Сформировать требования", "Спроектировать архитектуру и БД", "Реализовать модули пользователей, администратора, абонементов и отчетности", "Провести тестирование"]},
    {"title": "Предметная область", "bullets": ["Участники: клиент, тренер, администратор", "Процессы: регистрация, расписание, запись, абонементы, посещаемость", "Ключевая сложность: взаимосвязь клиента, занятия, тренера и тарифа", "Система должна поддерживать полный цикл обслуживания"]},
    {"title": "Требования к системе", "bullets": ["Регистрация и авторизация пользователей", "Просмотр тренировок и тренеров", "Запись и отмена записи на занятие", "Покупка, продление и заморозка абонемента", "Административное управление справочниками", "Аналитика и экспорт отчетов"]},
    {"title": "Диаграмма прецедентов", "bullets": ["Клиент работает с расписанием, записью и абонементами", "Администратор управляет пользователями, тренерами, занятиями и отчетами", "Диаграмма показывает границы системы и основные сценарии использования"], "image": "diagrams/use_case_diagram.png"},
    {"title": "Технологический стек", "bullets": ["Python и Flask — серверная часть", "SQLite и SQLAlchemy — хранение данных", "Flask-Login — авторизация", "Flask-WTF и WTForms — формы", "Flask-Mail — уведомления", "ReportLab и XlsxWriter — отчеты", "pytest — тестирование"]},
    {"title": "Архитектура проекта", "bullets": ["Приложение разделено на слои", "controllers — маршруты", "models — сущности БД", "forms — проверка ввода", "services — уведомления и отчеты", "templates/static — интерфейс"], "image": "diagrams/project_structure.png"},
    {"title": "База данных", "bullets": ["User — пользователь и роль", "Trainer — тренер", "WorkoutType — тип занятия", "Workout — тренировка в расписании", "Booking — запись пользователя", "Abonement и UserAbonement — тарифы и покупки"], "image": "diagrams/er_diagram.png"},
    {"title": "Пользовательский сценарий", "bullets": ["Регистрация и вход", "Просмотр расписания", "Фильтрация тренировок", "Просмотр карточки тренера", "Запись на занятие", "Просмотр личного расписания", "Работа с абонементом"]},
    {"title": "Административный сценарий", "bullets": ["Вход администратора", "Управление тренерами", "Управление типами тренировок", "Формирование расписания", "Управление пользователями", "Управление абонементами", "Просмотр аналитики"], "image": "diagrams/Controllers Class Diagram.png"},
    {"title": "Интерфейс: главная страница", "bullets": ["Публичный экран приложения до входа", "Доступ к тренировкам, входу и регистрации", "Визуальное представление пользовательского сервиса"], "image": "docs/screenshots/homepage.png"},
    {"title": "Интерфейс: посетитель", "bullets": ["Главная страница после авторизации", "Доступны тренировки, план, расписание и абонементы", "Верхнее меню отражает роль обычного пользователя"], "image": "docs/screenshots/homepage_user.png"},
    {"title": "Интерфейс: тренировки", "bullets": ["Экран от лица посетителя", "Показаны уведомления и пользовательские действия", "Сценарий ведет клиента к подбору плана и записи"], "image": "docs/screenshots/visitor_workouts.png"},
    {"title": "Интерфейс: администратор", "bullets": ["Административный режим после входа", "Переходы к клиентам, тренировкам и аналитике", "Раздел доступен только пользователю с ролью администратора"], "image": "docs/screenshots/admin_dashboard.png"},
    {"title": "Интерфейс: клиенты", "bullets": ["Табличное управление пользователями", "Отображаются статусы, активность и риск ухода", "Администратор может перейти к карточке клиента"], "image": "docs/screenshots/admin_users.png"},
    {"title": "Абонементы и уведомления", "bullets": ["Каталог тарифов", "Покупка абонемента", "Расчет срока действия и остатка посещений", "Продление и заморозка", "Уведомления о тренировках и состоянии абонемента"], "image": "diagrams/services_class.png"},
    {"title": "Аналитика и отчеты", "bullets": ["Популярность тренировок", "Загрузка тренеров", "Посещаемость", "Выбор периода отчета", "Экспорт в PDF и Excel", "Поддержка управленческих решений"]},
    {"title": "Тестирование", "bullets": ["pytest и тестовая SQLite БД в памяти", "Проверка главной страницы, входа и регистрации", "Проверка пользовательских маршрутов", "Проверка административного доступа", "Проверка моделей User, Workout и Booking"], "image": "diagrams/tests_class.png"},
    {"title": "Результат разработки", "bullets": ["Создана веб-ИС для фитнес-клуба", "Снижена ручная нагрузка администратора", "Централизованы расписание, клиенты и абонементы", "Добавлены аналитика и отчетность", "Архитектура допускает дальнейшее развитие"]},
    {"title": "Заключение", "bullets": ["Цель ВКР достигнута", "Разработаны пользовательская и административная части", "Реализованы абонементы, уведомления и отчеты", "Проведено тестирование ключевых сценариев", "Перспективы: онлайн-оплата, мобильная версия, кабинет тренера"]},
]


def build():
    OUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(SLIDES)))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("ppt/presentation.xml", presentation_xml(len(SLIDES)))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(SLIDES)))
        z.writestr("ppt/slideMasters/slideMaster1.xml", master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>')
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>')
        z.writestr("ppt/theme/theme1.xml", theme_xml())
        for i, slide in enumerate(SLIDES, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(slide, i))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rels(bool(slide.get("image")), i))
            if slide.get("image"):
                z.write(ROOT / slide["image"], f"ppt/media/image{i}.png")
    print(OUT)


if __name__ == "__main__":
    build()
