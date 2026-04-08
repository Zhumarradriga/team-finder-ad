from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from consts import (
    ABOUT_MAX_LENGTH,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    SURNAME_MAX_LENGTH,
)
from services import generate_avatar
from users.managers import UserManager
from validators import validate_github_url


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
        blank=True, verbose_name="GitHub", validators=[validate_github_url]
    )
    about = models.TextField(
        max_length=ABOUT_MAX_LENGTH,
        blank=True,
        verbose_name="О себе",
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
