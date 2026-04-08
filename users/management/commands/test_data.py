"""Management command для заполнения базы тестовыми данными из JSON.

Usage:
    python manage.py seed_test_data                                          # базовый запуск
    python manage.py seed_test_data --data-file staging_data.json           # кастомный файл
    python manage.py seed_test_data --force                                  # пересоздать
    python manage.py seed_test_data --password MyPass123                     # кастомный пароль
    python manage.py seed_test_data --count 5                                # 5 проектов
    python manage.py seed_test_data dev --skills Python Django               # с фильтрами
    python manage.py seed_test_data --help                                   # показать справку
"""

import argparse
import json
from pathlib import Path
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from projects.models import Project, Skill

User = get_user_model()


class Command(BaseCommand):
    """Команда для создания тестовых данных из JSON с гибкой настройкой."""

    help = "Создаёт тестовых пользователей и проекты из JSON-файла"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--data-file",
            type=str,
            default="fixtures/test_data.json",
            help="Путь к JSON-файлу с данными (относительно MEDIA_ROOT или абсолютный)",
        )
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

    def _resolve_data_path(self, filename: str) -> Path:
        """Преобразует имя файла в абсолютный путь."""
        path = Path(filename)
        if path.is_absolute():
            return path
        # Сначала пробуем относительно MEDIA_ROOT, затем BASE_DIR
        for base in [getattr(settings, "MEDIA_ROOT", None), settings.BASE_DIR]:
            if base:
                candidate = Path(base) / filename
                if candidate.exists():
                    return candidate
        # Если не нашли — возвращаем как есть (ошибка будет при чтении)
        return path

    def _load_data(self, filepath: Path) -> dict[str, Any]:
        """Загружает и валидирует JSON-файл."""
        if not filepath.exists():
            raise CommandError(f"Файл не найден: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Ошибка парсинга JSON: {e}")

        # Базовая валидация структуры
        required_keys = {"users", "skills", "projects"}
        if not required_keys.issubset(data.keys()):
            raise CommandError(
                f"JSON должен содержать ключи: {required_keys}. "
                f"Получено: {set(data.keys())}"
            )
        return data

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        # Загрузка данных
        data_path = self._resolve_data_path(options["data_file"])
        self.stdout.write(f"Загрузка данных из: {data_path}")
        data = self._load_data(data_path)

        # Параметры
        force = options["force"]
        password = options["password"]
        count = options["count"]
        environment = options["environment"]
        skills_filter: Optional[list[str]] = options["skills"]
        users_only = options["users_only"]
        prefix = "" if environment == "dev" else f"{environment}_"

        # Проверка на существующие данные
        test_email = f"{prefix}{data['users'][0]['email']}" if data["users"] else None
        if test_email and User.objects.filter(email=test_email).exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Тестовые данные для '{environment}' уже существуют. "
                    "Используйте --force для пересоздания."
                )
            )
            return

        # При --force: удаляем старые тестовые данные
        if force:
            self._cleanup_test_data(prefix, data)
            self.stdout.write("Старые тестовые данные удалены.")

        # Создание пользователей
        self.stdout.write(f"Создание пользователей (окружение: {environment})...")
        users_map = {}
        for user_data in data["users"]:
            email = f"{prefix}{user_data['email']}"
            user = self._create_user(
                email=email,
                password=password,
                name=user_data.get("name", ""),
                surname=user_data.get("surname", ""),
                about=user_data.get("about", ""),
                github_url=user_data.get("github_url", ""),
                is_active=user_data.get("is_active", True),
            )
            users_map[user_data["email"]] = user
            self.stdout.write(f"  ✓ Пользователь: {email}")

        if users_only:
            self.stdout.write(self.style.SUCCESS("Только пользователи созданы."))
            return

        # Создание навыков (с фильтрацией, если указано)
        all_skills = [s["name"] for s in data["skills"]]
        if skills_filter:
            all_skills = [s for s in all_skills if s[0] in skills_filter]
            self.stdout.write(f"Фильтр навыков: {', '.join(skills_filter)}")

        skills_map = {}
        for name in all_skills:
            skill, created = Skill.objects.get_or_create(
                name=f"{prefix}{name}",
            )
            skills_map[name] = skill
            if created:
                self.stdout.write(f"  ✓ Навык: {skill.name}")

        # Создание проектов
        projects_config = []
        for proj in data["projects"]:
            owner_email = proj.get("owner_email")
            if owner_email not in users_map:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Проект '{proj['name']}' пропущен: владелец '{owner_email}' не найден"
                    )
                )
                continue
            projects_config.append(
                {
                    "name": proj["name"],
                    "desc": proj.get("description", ""),
                    "owner": users_map[owner_email],
                    "skills": proj.get("skills", []),
                    "github": proj.get("github_url", ""),
                    "status": proj.get("status", "OPEN"),
                }
            )

        for config in projects_config[:count]:
            project = Project.objects.create(
                name=f"{prefix}{config['name']}",
                description=config["desc"],
                owner=config["owner"],
                github_url=config["github"],
                status=getattr(Project.Status, config["status"], "open"),
            )
            # Привязываем только существующие навыки
            valid_skills = [
                skills_map[sk] for sk in config["skills"] if sk in skills_map
            ]
            if valid_skills:
                project.skills.set(valid_skills)
            project.participants.add(config["owner"])
            self.stdout.write(f"  ✓ Проект: {project.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово! Создано: {len(users_map)} пользователей, "
                f"{min(count, len(projects_config))} проектов."
            )
        )

    def _create_user(self, email: str, password: str, **kwargs) -> User:
        """Вспомогательный метод для создания пользователя."""
        return User.objects.create_user(email=email, password=password, **kwargs)

    def _cleanup_test_data(self, prefix: str, data: dict[str, Any]) -> None:
        """Удаляет тестовые данные с указанным префиксом."""
        # Удаляем проекты
        project_names = [f"{prefix}{p['name']}" for p in data.get("projects", [])]
        if project_names:
            Project.objects.filter(name__in=project_names).delete()

        # Удаляем навыки
        skill_names = [f"{prefix}{s['name']}" for s in data.get("skills", [])]
        if skill_names:
            Skill.objects.filter(name__in=skill_names).delete()

        # Удаляем пользователей
        user_emails = [f"{prefix}{u['email']}" for u in data.get("users", [])]
        if user_emails:
            User.objects.filter(email__in=user_emails).delete()
