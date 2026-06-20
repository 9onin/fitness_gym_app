from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIAGRAMS = ROOT / "diagrams"
SHOTS = DOCS / "screenshots"


def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


TITLE = font(34, True)
HEAD = font(22, True)
BODY = font(18)
SMALL = font(15)


def text(draw, xy, value, fill="#0f172a", fnt=BODY, max_width=None, line_gap=6):
    x, y = xy
    if max_width:
        lines = []
        approx = max(10, max_width // max(8, fnt.size // 2))
        for part in str(value).split("\n"):
            lines.extend(wrap(part, approx) or [""])
    else:
        lines = str(value).split("\n")
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def rounded(draw, box, fill, outline=None, width=2, radius=14):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, start, end, fill="#475569", width=3):
    draw.line([start, end], fill=fill, width=width)
    ex, ey = end
    sx, sy = start
    dx = ex - sx
    dy = ey - sy
    if abs(dx) > abs(dy):
        points = [(ex, ey), (ex - 12 if dx > 0 else ex + 12, ey - 7), (ex - 12 if dx > 0 else ex + 12, ey + 7)]
    else:
        points = [(ex, ey), (ex - 7, ey - 12 if dy > 0 else ey + 12), (ex + 7, ey - 12 if dy > 0 else ey + 12)]
    draw.polygon(points, fill=fill)


def draw_actor(draw, x, y, label):
    draw.ellipse((x + 24, y, x + 56, y + 32), outline="#0f172a", width=3)
    draw.line((x + 40, y + 32, x + 40, y + 86), fill="#0f172a", width=3)
    draw.line((x + 6, y + 52, x + 74, y + 52), fill="#0f172a", width=3)
    draw.line((x + 40, y + 86, x + 12, y + 126), fill="#0f172a", width=3)
    draw.line((x + 40, y + 86, x + 68, y + 126), fill="#0f172a", width=3)
    tw = draw.textlength(label, font=HEAD)
    draw.text((x + 40 - tw / 2, y + 140), label, font=HEAD, fill="#0f172a")


def use_case_diagram():
    DIAGRAMS.mkdir(exist_ok=True)
    img = Image.new("RGB", (1600, 1000), "#ffffff")
    d = ImageDraw.Draw(img)
    text(d, (455, 34), "Use Case Diagram: Fitness Gym App", fnt=TITLE, fill="#303030")
    rounded(d, (345, 118, 1255, 890), "#ffffff", "#e8b6ff", 3, 0)
    d.rectangle((345, 118, 1255, 180), fill="#fff3dc", outline="#e8b6ff", width=3)
    text(d, (655, 136), "Fitness Gym App", fnt=HEAD, fill="#303030")
    draw_actor(d, 88, 345, "User")
    draw_actor(d, 1395, 345, "Admin")
    cases = [
        (430, 235, "Login / Register"),
        (430, 385, "View workouts"),
        (430, 535, "Book workout"),
        (430, 685, "Buy abonement"),
        (705, 460, "View schedule"),
        (955, 285, "Manage users"),
        (955, 475, "Manage workouts\nand trainers"),
        (955, 665, "View analytics\nand reports"),
    ]
    centers = {}
    for x, y, label in cases:
        d.ellipse((x, y, x + 225, y + 98), fill="#fff8e8", outline="#f1d8b5", width=3)
        centers[label] = (x + 110, y + 48)
        text(d, (x + 28, y + 24), label, fnt=SMALL, max_width=172, fill="#303030", line_gap=2)
    client = (210, 463)
    admin = (1390, 463)
    for key in ["Login / Register", "View workouts", "Buy abonement", "Book workout", "View schedule"]:
        d.line([client, (centers[key][0] - 112, centers[key][1])], fill="#303030", width=3)
    for key in ["Manage users", "Manage workouts\nand trainers", "View analytics\nand reports", "Login / Register"]:
        d.line([admin, (centers[key][0] + 112, centers[key][1])], fill="#303030", width=3)
    d.line([(652, 583), (705, 508)], fill="#303030", width=2)
    text(d, (650, 535), "<<include>>", fnt=SMALL, fill="#303030")
    img.save(DIAGRAMS / "use_case_diagram.png")


def browser_frame(title, subtitle, cards, filename, accent="#2563eb"):
    SHOTS.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1365, 900), "#eef2f7")
    d = ImageDraw.Draw(img)
    rounded(d, (34, 34, 1331, 866), "#ffffff", "#cbd5e1", 2, 18)
    rounded(d, (34, 34, 1331, 88), "#0f172a", None, 1, 18)
    for i, c in enumerate(["#ef4444", "#f59e0b", "#22c55e"]):
        d.ellipse((58 + i * 28, 54, 74 + i * 28, 70), fill=c)
    text(d, (160, 52), "fitness-gym.local", fnt=SMALL, fill="#dbeafe")
    rounded(d, (34, 88, 1331, 158), "#ffffff", "#e2e8f0", 1, 0)
    text(d, (74, 112), "Fitness Gym App", fnt=HEAD, fill="#0f172a")
    for x, item in [(950, "Тренировки"), (1060, "Абонементы"), (1188, "Войти")]:
        text(d, (x, 116), item, fnt=SMALL, fill="#334155")
    rounded(d, (74, 198, 1291, 376), "#111827", None, 1, 20)
    d.rectangle((74, 198, 1291, 376), fill="#111827")
    text(d, (118, 236), title, fnt=TITLE, fill="#ffffff", max_width=690)
    text(d, (120, 292), subtitle, fnt=BODY, fill="#d1d5db", max_width=720)
    rounded(d, (1040, 250, 1218, 306), accent, None, 1, 10)
    text(d, (1076, 266), "Перейти", fnt=BODY, fill="#ffffff")
    y = 420
    for row in range(2):
        for col in range(2):
            idx = row * 2 + col
            if idx >= len(cards):
                continue
            x = 74 + col * 610
            rounded(d, (x, y, x + 570, y + 170), "#ffffff", "#cbd5e1", 2, 12)
            rounded(d, (x + 24, y + 26, x + 86, y + 88), accent, None, 1, 10)
            text(d, (x + 110, y + 26), cards[idx][0], fnt=HEAD, fill="#0f172a", max_width=390)
            text(d, (x + 110, y + 68), cards[idx][1], fnt=BODY, fill="#475569", max_width=400)
        y += 205
    img.save(SHOTS / filename)


def screenshots():
    browser_frame(
        "Главная страница фитнес-клуба",
        "Быстрый доступ к тренировкам, тренерам, абонементам и личному расписанию клиента.",
        [
            ("Ближайшие занятия", "Карточки занятий с датой, временем и количеством свободных мест."),
            ("Тренеры", "Переход к профилям специалистов и их направлениям."),
            ("Абонементы", "Просмотр тарифов, покупка, продление и заморозка."),
            ("Личный кабинет", "Записи, уведомления и история посещений."),
        ],
        "homepage.png",
        "#2563eb",
    )
    browser_frame(
        "Авторизация пользователя",
        "Форма входа проверяет почту, пароль и контрольный ответ перед созданием сессии.",
        [
            ("Email и пароль", "Обязательные поля с серверной проверкой."),
            ("Капча", "Простая защита формы от автоматического ввода."),
            ("Запомнить меня", "Поддержка удобного повторного входа."),
            ("Регистрация", "Переход к созданию новой учетной записи."),
        ],
        "login.png",
        "#16a34a",
    )
    browser_frame(
        "Каталог абонементов",
        "Пользователь сравнивает тарифы по цене, сроку действия, посещениям и доступным возможностям.",
        [
            ("Базовый", "Оптимальный тариф для знакомства с клубом."),
            ("Стандарт", "Регулярные тренировки и основные услуги."),
            ("Премиум", "Расширенные возможности и приоритетные условия."),
            ("Заморозка", "Учет периода временной приостановки абонемента."),
        ],
        "abonements.png",
        "#dc2626",
    )
    browser_frame(
        "Сравнение абонементов",
        "Табличное представление помогает выбрать подходящий тариф по ключевым параметрам.",
        [
            ("Цена", "Сравнение стоимости и цены одного посещения."),
            ("Срок", "Количество дней действия каждого тарифа."),
            ("Посещения", "Доступный лимит или безлимитный формат."),
            ("Преимущества", "Список включенных возможностей для клиента."),
        ],
        "compare.png",
        "#7c3aed",
    )


if __name__ == "__main__":
    use_case_diagram()
    print(DIAGRAMS / "use_case_diagram.png")
