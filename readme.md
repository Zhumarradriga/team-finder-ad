# TeamFinder

Платформа для поиска участников для  своих проектов. Зарегистрированные пользователи могут публиковать свои проекты, находить команду для них и откликаться на понравившиеся опубликованные предложения.

Также был реализован функционал  навыков проектов и фильтрация по навыкам.(Вариант 3)

## Функциональность

- Регистрация и аутентификация пользователей (по email и паролю)
- Публичные профили пользователей с информацией о пользователе и списком проектов
- Создание, редактирование  проектов
- Возможность подписываться  на участие в проектах других пользователей
- Добавление списка навыков с помощью системы тегов
- Фильтрация проектов по навыкам
- Смена пароля
- Генерация аватара при регистрации

## Стек технологий

- Python 3.14
- Django 5.2
- PostgreSQL 16
- Docker / Docker-Compose

## Запуск проекта

### 1. Виртуальное окружение
```bash
python -m venv .venv
```

Windows (PowerShell):
```bash
.venv\Scripts\Activate
```

Linux/Mac:
```bash
source .venv/bin/activate
```
```bash
pip install -r ./requirements.txt
```

### 2. Файл `.env`
```bash
cp .env_example .env
```

Заполнить `.env` следующими значениями:
```
DJANGO_SECRET_KEY=very-secret-key
DJANGO_DEBUG=True
POSTGRES_DB=team_finder
POSTGRES_USER=team_finder
POSTGRES_PASSWORD=team_finder
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### 3. Развертывание Базы данных
```bash
docker compose up -d
```

### 4. Приминение миграций и запуск
```bash
python manage.py migrate
python manage.py runserver
```

### 5. Запуск тестов
```bash
python manage.py test
```
Или более подробный вывод
```bash
python manage.py test -v 2
```

### 6. Тестовые данные

Для заполнения базы тестовыми пользователями и проектами используется команда `test_data`:

```bash
python manage.py test_data
```

#### Аргументы команды `test_data`

| Аргумент | Тип | Описание | Значение по умолчанию |
|----------|-----|----------|----------------------|
| `environment` | позиционный | Окружение: `dev` (по умолчанию), `staging`, `prod`. Влияет на префиксы данных (например, email `alice@example.com` для dev или `staging_alice@example.com` для staging) | `dev` |
| `--force` | флаг | Пересоздать данные, удалив существующие тестовые записи с таким же префиксом | нет |
| `--password` | строка | Пароль для всех тестовых пользователей | `testpass123` |
| `--count` | число | Количество проектов для создания. Доступные значения: `1`, `3`, `5`, `10` | `3` |
| `--skills` | список строк | Ограничить набор навыков для проектов. Например: `--skills Python Django` создаст проекты только с этими навыками | все навыки |
| `--users-only` | флаг | Создать только пользователей, без проектов и навыков | нет |

#### Примеры использования

**Базовый запуск** (создаёт 3 пользователя и 3 проекта):
```bash
python manage.py test_data
```

**Пересоздать данные** (удалить старые и создать заново):
```bash
python manage.py test_data --force
```

**Задать кастомный пароль** для всех пользователей:
```bash
python manage.py test_data --password MyPass123
```

**Создать больше проектов** (5 штук):
```bash
python manage.py test_data --count 5
```

**Ограничить навыки** (только Python и Django):
```bash
python manage.py test_data --skills Python Django
```

**Создать только пользователей** (без проектов и навыков):
```bash
python manage.py test_data --users-only
```

**Запуск для другого окружения** (staging):
```bash
python manage.py test_data staging
```

**Комбинированный пример** (окружение dev, 5 проектов, кастомный пароль):
```bash
python manage.py test_data dev --count 5 --password SecurePass123
```

#### Создаваемые тестовые данные

По умолчанию (`python manage.py test_data`) создаются:

**3 пользователя:**

| Email | Пароль |
|-------|--------|
| alex@alex.com | testpass123 |
| bob@bob.com | testpass123 |
| carl@carl.com | testpass123 |

**Навыки:**
- Python
- React
- Django
- Figma
- TypeScript

**Проекты** (3 шт. по умолчанию):
1. Трекер задач (владелец: alice, навыки: Python, Django)
2. Портфолио-генератор (владелец: bob, навыки: React, TypeScript)
3. Дизайн-система (владелец: carol, навыки: Figma, React)

> При использовании аргумента `--count` количество проектов увеличивается согласно значению (максимум 10).

### 6. Админ панель и создание супер пользователя
```bash
python manage.py createsuperuser
```

Доступ к админ панели можно получить по ссылке: http://localhost:8000/admin/

## Автор

Красильников Александр Викторович студент группы 8К21