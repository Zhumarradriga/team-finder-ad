"""Management command для заполнения базы тестовыми данными.

Usage:
    python manage.py seed_test_data                          # базовый запуск
    python manage.py seed_test_data --force                  # пересоздать
    python manage.py seed_test_data --password MyPass123     # кастомный пароль
    python manage.py seed_test_data --count 5                # 5 проектов
    python manage.py seed_test_data dev --skills Python Django  # с фильтрами
    python manage.py seed_test_data --help                   # показать справку
"""

import argparse
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill

User = get_user_model()


class Command(BaseCommand):
    """Команда для создания тестовых данных с гибкой настройкой."""

    help = "Создаёт тестовых пользователей и проекты"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Пересоздать данные, удалив существующие тестовые записи",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="testpass123",
            help="Пароль для всех тестовых пользователей (по умолчанию: testpass123)",
        )
        parser.add_argument(
            "--count",
            type=int,
            choices=[1, 3, 5, 10],
            default=3,
            help="Количество проектов для создания: 1, 3, 5 или 10 (по умолчанию: 3)",
        )
        parser.add_argument(
            "--skills",
            nargs="+",
            type=str,
            help="Ограничить набор навыков для проектов (например: --skills Python React)",
        )
        parser.add_argument(
            "--users-only",
            action="store_true",
            help="Создать только пользователей, без проектов и навыков",
        )
        parser.add_argument(
            "environment",
            nargs="?",
            choices=["dev", "staging", "prod"],
            default="dev",
            help="Окружение: dev (по умолчанию), staging, prod (влияет на префиксы данных)",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        force = options["force"]
        password = options["password"]
        count = options["count"]
        environment = options["environment"]
        skills_filter: Optional[list[str]] = options["skills"]
        users_only = options["users_only"]

        # Префикс для данных в зависимости от окружения
        prefix = "" if environment == "dev" else f"{environment}_"

        # Проверка на существующие данные
        test_email = f"{prefix}alice@example.com"
        if User.objects.filter(email=test_email).exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Тестовые данные для '{environment}' уже существуют. "
                    "Используйте --force для пересоздания."
                )
            )
            return

        # При --force: удаляем старые тестовые данные
        if force:
            self._cleanup_test_data(prefix)
            self.stdout.write("Старые тестовые данные удалены.")

        # Создание пользователей
        self.stdout.write(f"Создание пользователей (окружение: {environment})...")
        alex = self._create_user(
            email=f"{prefix}alex@alex.com",
            name="Алекс",
            surname="Тумба",
            password=password,
            about="Фронтенд-разработчик, люблю React и TypeScript.",
            github_url="https://github.com/alice",
        )
        bob = self._create_user(
            email=f"{prefix}bob@bob.com",
            name="Боб",
            surname="Бобович",
            password=password,
            about="Бэкенд-разработчик, Python/Django.",
            github_url="https://github.com/bob",
        )
        carl = self._create_user(
            email=f"{prefix}carl@carl.com",
            name="Карл",
            surname="Штейн",
            password=password,
            about="UI/UX дизайнер, TypeScript",
        )

        if users_only:
            self.stdout.write(self.style.SUCCESS("Только пользователи созданы."))
            return

        # Создание навыков (с фильтрацией, если указано)
        all_skills = [
            ("Python", "Язык программирования"),
            ("React", "Frontend-фреймворк"),
            ("Django", "Backend-фреймворк"),
            ("Figma", "Инструмент дизайна"),
            ("TypeScript", "Типизированный JavaScript"),
        ]
        if skills_filter:
            all_skills = [s for s in all_skills if s[0] in skills_filter]
            self.stdout.write(f"Фильтр навыков: {', '.join(skills_filter)}")

        skills_map = {}
        for name, desc in all_skills:
            skill, created = Skill.objects.get_or_create(
                name=f"{prefix}{name}",
                defaults={"name": f"{prefix}{name}"},  # если добавите описание
            )
            skills_map[name] = skill
            if created:
                self.stdout.write(f"  ✓ Навык: {skill.name}")

        # Создание проектов (количество по аргументу --count)
        projects_config = [
            {
                "name": "Трекер задач",
                "desc": "Простое приложение для отслеживания задач в команде.",
                "owner": alex,
                "skills": ["Python", "Django"],
                "github": "https://github.com/alice/task-tracker",
            },
            {
                "name": "Портфолио-генератор",
                "desc": "Сервис для автоматической генерации портфолио по GitHub.",
                "owner": bob,
                "skills": ["React", "TypeScript"],
                "github": "https://github.com/bob/portfolio-gen",
            },
            {
                "name": "Дизайн-система",
                "desc": "Набор UI-компонентов и гайдлайнов.",
                "owner": carl,
                "skills": ["Figma", "React"],
                "github": "",
            },
            {
                "name": "API для мобильного приложения",
                "desc": "REST API с аутентификацией, пагинацией и кэшированием.",
                "owner": bob,
                "skills": ["Python", "Django"],
                "github": "https://github.com/bob/mobile-api",
            },
            {
                "name": "Дашборд аналитики",
                "desc": "Визуализация метрик проекта в реальном времени.",
                "owner": alex,
                "skills": ["React", "TypeScript", "Figma"],
                "github": "https://github.com/alice/analytics-dashboard",
            },
            {
                "name": "test1",
                "desc": "test1",
                "owner": carl,
                "skills": ["React", "TypeScript", "Figma"],
                "github": "https://github.com/alice/analytics-dashboard",
            },
            {
                "name": "test2",
                "desc": "test2",
                "owner": carl,
                "skills": ["React", "TypeScript", "Figma"],
                "github": "https://github.com/alice/analytics-dashboard",
            },
            {
                "name": "test3",
                "desc": "test3",
                "owner": carl,
                "skills": ["React", "TypeScript", "Figma"],
                "github": "https://github.com/alice/analytics-dashboard",
            },
            {
                "name": "test4",
                "desc": "test4",
                "owner": carl,
                "skills": ["React", "TypeScript", "Figma"],
                "github": "https://github.com/alice/analytics-dashboard",
            },
            {
                "name": "test5",
                "desc": "test5",
                "owner": carl,
                "skills": ["React", "TypeScript", "Figma"],
                "github": "https://github.com/alice/analytics-dashboard",
            },
        ]
        # Обрезаем список по аргументу --count
        for config in projects_config[:count]:
            project = Project.objects.create(
                name=f"{prefix}{config['name']}",
                description=config["desc"],
                owner=config["owner"],
                github_url=config["github"],
                status=getattr(Project.Status, "OPEN", "open"),
            )
            # Привязываем только те навыки, которые есть в skills_map
            valid_skills = [
                skills_map[sk] for sk in config["skills"] if sk in skills_map
            ]
            if valid_skills:
                project.skills.set(valid_skills)
            project.participants.add(config["owner"])
            self.stdout.write(f"  ✓ Проект: {project.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово! Создано: 3 пользователя, {min(count, len(projects_config))} проектов."
            )
        )

    def _create_user(self, email: str, password: str, **kwargs) -> User:
        """Вспомогательный метод для создания пользователя."""
        return User.objects.create_user(email=email, password=password, **kwargs)

    def _cleanup_test_data(self, prefix: str) -> None:
        """Удаляет тестовые данные с указанным префиксом."""
        # Удаляем проекты (M2M очистится автоматически через CASCADE)
        Project.objects.filter(name__startswith=prefix).delete()
        # Удаляем навыки
        Skill.objects.filter(name__startswith=prefix).delete()
        # Удаляем пользователей
        User.objects.filter(email__contains=f"{prefix}alice@").delete()
        User.objects.filter(email__contains=f"{prefix}bob@").delete()
        User.objects.filter(email__contains=f"{prefix}carol@").delete()
