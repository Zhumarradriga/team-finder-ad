import io
import random

from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from PIL import Image, ImageDraw, ImageFont

from consts import (
    AVATAR_ANCHOR_X,
    AVATAR_ANCHOR_Y,
    AVATAR_COLORS,
    AVATAR_FONT_SIZE,
    AVATAR_SIZE,
    PROJECTS_PAG,
)


def paginate(queryset, request, pagination=PROJECTS_PAG):
    """Пагинация"""
    paginator = Paginator(queryset, pagination)
    return paginator.get_page(request.GET.get("page"))


def normalize_phone(phone: str) -> str:
    if phone.startswith("8"):
        return "+7" + phone[1:]
    return phone


def generate_avatar(letter: str) -> ContentFile:
    """Генерирует квадратное изображение-аватар с заданной буквой.

    Создаёт PNG-файл случайного цвета из `AVATAR_COLORS`, центрирует
    заглавную букву и возвращает его в формате, готовом для сохранения
    в `ImageField`.

    Args:
        letter: Символ для отображения на аватаре.

    Returns:
        ContentFile: Бинарное содержимое PNG-изображения.

    Note:
        Использует каскадный поиск шрифтов для кроссплатформенной совместимости.
    """
    size = AVATAR_SIZE
    color = random.choice(AVATAR_COLORS)

    img = Image.new("RGB", (size, size), color=color)
    draw = ImageDraw.Draw(img)

    font_size = AVATAR_FONT_SIZE
    font = None

    # Кандидаты для Times New Roman под разные ОС
    font_candidates = [
        "Times New Roman",  # Windows/macOS (системный резолвер)
        "C:/Windows/Fonts/timesbd.ttf",  # Windows Bold
        "C:/Windows/Fonts/times.ttf",  # Windows Regular
        "/System/Library/Fonts/Times New Roman.ttf",  # macOS
        "/Library/Fonts/Times New Roman.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",  # Linux
    ]

    for path in font_candidates:
        try:
            font = ImageFont.truetype(path, font_size)
            break  # Берём первый доступный шрифт
        except OSError:
            continue

    # Фоллбэк на встроенный шрифт Pillow (>= 8.0.0)
    if font is None:
        font = ImageFont.load_default(size=font_size)

    text = letter.upper()
    bbox = draw.textbbox((AVATAR_ANCHOR_X, AVATAR_ANCHOR_Y), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2 - bbox[0]
    y = (size - text_height) / 2 - bbox[1]
    draw.text((x, y), text, fill="white", font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())
