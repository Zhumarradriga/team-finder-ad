from django.conf import settings
from django.db import models

SKILL_MAX_LENGTH = 124
PROJECT_NAME_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6

class ProjectManager(models.Manager):
    def open(self):
        """Все открытые проекты, готовые к участию."""
        return self.filter(status="open")
    
    def closed(self):
        """Все завершённые проекты."""
        return self.filter(status="closed")
    
    def by_owner(self, user):
        """Проекты, созданные конкретным пользователем."""
        return self.filter(owner=user)
    
    def with_participant(self, user):
        """Проекты, в которых пользователь участвует (включая свои)."""
        return self.filter(
            models.Q(owner=user) | models.Q(participants=user)
        ).distinct()


class Skill(models.Model):
    """Модель навыка (технологии, инструмента, компетенции).

    Используется для тегирования проектов и фильтрации списка
    проектов по требуемым навыкам.

    Attributes:
        name: Уникальное название навыка (например, "Python", "Django").
    """
    name = models.CharField(
        max_length=SKILL_MAX_LENGTH,
        unique=True,
        verbose_name="Название навыка",
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    """Модель проекта, создаваемого пользователем для коллаборации.

    Представляет инициативу, в которой могут участвовать несколько
    разработчиков. Поддерживает базовый жизненный цикл через статусы
    и привязку к требуемым навыкам.

    Attributes:
        name: Краткое название проекта (макс. 200 символов).
        description: Подробное описание (опционально).
        owner: Пользователь-создатель. Связь `CASCADE`: при удалении
            пользователя его проекты также удаляются.
        created_at: Дата и время создания (автозаполнение).
        github_url: Ссылка на репозиторий (опционально).
        status: Текущий статус: "open" или "closed".
        participants: ManyToMany с пользователями. Пустой по умолчанию.
        skills: ManyToMany с навыками. Пустой по умолчанию.
    """
    objects = ProjectManager()

    
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField(
        max_length=PROJECT_NAME_MAX_LENGTH,
        verbose_name="Название проекта",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание проекта",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор проекта",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания проекта",
    )
    github_url = models.URLField(
        blank=True,
        verbose_name="ссылка на GitHub",
    )
    status = models.CharField(
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Статус проекта",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники проекта",
    )
    skills = models.ManyToManyField(
        Skill,
        related_name="projects",
        blank=True,
        verbose_name="Навыки",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.name