import io
import random

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont


from users.managers import UserManager

AVATAR_COLORS = [
    "#2768FFD3",
    "#FF3E3E",
    "#50FF67",
    "#FFC53F",
    "#A78BFA",
    "#FF9244",
    "#2DC7E2",
    "#FF3B9D",
    "#BBFF56",
    "#FFAB67",
]
AVATAR_FONT_SIZE = 100
ABOUT_MAX_LENGTH = 256
AVATAR_SIZE = 200
NAME_MAX_LENGTH = 124
PHONE_MAX_LENGTH = 12
SURNAME_MAX_LENGTH = 124

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
        "Times New Roman",                     # Windows/macOS (системный резолвер)
        "C:/Windows/Fonts/timesbd.ttf",        # Windows Bold
        "C:/Windows/Fonts/times.ttf",          # Windows Regular
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
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2 - bbox[0]
    y = (size - text_height) / 2 - bbox[1]
    draw.text((x, y), text, fill="white", font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя для аутентификации и профиля.

    Заменяет стандартную `django.contrib.auth.models.User`.
    Использует email как основной идентификатор, поддерживает
    профилирование, загрузку аватаров и список избранных проектов.

    Attributes:
        email: Уникальный email (используется как `USERNAME_FIELD`).
        name / surname: Имя и фамилия.
        avatar: Файл изображения. Генерируется автоматически при создании.
        phone / github_url / about: Дополнительные поля профиля.
        favorites: ManyToMany-связь с проектами (`related_name="interested_users"`).
        is_active / is_staff: Флаги статуса и прав администратора.
    """
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        verbose_name="Имя",
    )
    surname = models.CharField(
        max_length=SURNAME_MAX_LENGTH,
        verbose_name="Фамилия",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        verbose_name="Аватар",
    )
    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        verbose_name="Телефон",
    )
    github_url = models.URLField(
        blank=True,
        verbose_name="GitHub",
    )
    about = models.TextField(
        max_length=ABOUT_MAX_LENGTH,
        blank=True,
        verbose_name="О себе",
    )
    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
        verbose_name="Избранные проекты",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Администратор",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} {self.surname} ({self.email})"

    def save(self, *args, **kwargs):
        """Сохраняет пользователя и генерирует аватар при первом создании.

        Автогенерация срабатывает только если:
        - Это новый объект (`self.pk is None`)
        - Аватар не был загружен вручную

        Note:
            `self.avatar.save(..., save=False)` сохраняет файл в хранилище,
            но НЕ вызывает `Model.save()`. Это предотвращает бесконечную рекурсию.
            Сама запись в БД происходит при вызове `super().save()`.
        """
        if not self.pk and not self.avatar:
            letter = self.name[0] if self.name else "U"
            avatar_content = generate_avatar(letter)
            filename = f"avatar_{self.email.split('@')[0]}.png"
            self.avatar.save(filename, avatar_content, save=False)
        super().save(*args, **kwargs)