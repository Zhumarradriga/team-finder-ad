import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from consts import SKILLS_AUTOCOMPLETE_LIMIT
from projects.forms import ProjectForm
from projects.models import Project, Skill
from services import paginate


def project_list_view(request):
    """Отображает список проектов с пагинацией и фильтрацией по навыку.

    Поддерживает фильтрацию через GET-параметр `?skill=<name>`.
    Оптимизировано через `select_related` и `prefetch_related`.

    Args:
        request: HTTP-запрос.

    Returns:
        Отрендеренный HTML-шаблон с объектом страницы, списком навыков
        и активным фильтром.
    """
    projects = Project.objects.select_related("owner").prefetch_related("participants")
    all_skills = Skill.objects.order_by("name").values_list("name", flat=True)
    active_skill = request.GET.get("skill", "").strip()

    if active_skill:
        projects = projects.filter(skills__name=active_skill)

    page_obj = paginate(projects, request)

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj,
            "all_skills": all_skills,
            "active_skill": active_skill,
        },
    )


def project_detail_view(request, project_id):
    """Отображает детальную страницу проекта.

    Загружает проект с связанными данными (владелец, участники, навыки).
    Возвращает 404, если проект не найден.
    """
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related(
            "participants", "skills"
        ),
        pk=project_id,
    )
    return render(
        request,
        "projects/project-details.html",
        {"project": project},
    )


@login_required
def create_project_view(request):
    """Создаёт новый проект и назначает текущего пользователя владельцем.

    Автоматически добавляет создателя в участники проекта.
    Перенаправляет на страницу проекта после успешного сохранения.
    """
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", project_id=project.pk)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
def edit_project_view(request, project_id):
    """Редактирует существующий проект.

    Доступно только владельцу проекта. При попытке доступа к чужому
    проекту `get_object_or_404` сразу вернёт 404.
    """
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        return redirect("projects:detail", project_id=project.pk)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@login_required
@require_POST
def complete_project_view(request, project_id):
    """Завершает проект (меняет статус на CLOSED).

    Требования:
    - Только для владельца проекта
    - Проект должен быть в статусе OPEN
    - Только POST-запрос

    Returns:
        JSON со статусом операции и новым статусом проекта.
        403 Forbidden при попытке закрыть чужой проект.
        400 Bad Request если проект уже закрыт.
    """
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user:
        return JsonResponse(
            {"status": "error", "detail": "Forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )
    if project.status != Project.Status.OPEN:
        return JsonResponse(
            {"status": "error", "detail": "Already closed"},
            status=HTTPStatus.BAD_REQUEST,
        )
    project.status = Project.Status.CLOSED
    project.save()
    return JsonResponse({"status": "ok", "project_status": "closed"})


@login_required
@require_POST
def toggle_participate_view(request, project_id):
    """Переключает участие текущего пользователя в проекте.

    Владелец проекта не может участвовать в нём (возвращает 400).
    Добавляет или удаляет пользователя из `participants`.

    Returns:
        JSON с текущим статусом участия (`participant: bool`).
    """
    project = get_object_or_404(Project, pk=project_id)
    user = request.user
    if project.owner == user:
        return JsonResponse(
            {
                "status": "error",
                "detail": "Owner cannot toggle participate",
            },
            status=HTTPStatus.BAD_REQUEST,
        )
    if participating := project.participants.filter(pk=user.pk).exists():
        project.participants.remove(user)
    else:
        project.participants.add(user)
    return JsonResponse({"status": "ok", "participant": participating})


def skills_autocomplete_view(request):
    """Возвращает список навыков для автодополнения.

    Фильтрует навыки по началу строки (`name__istartswith`).
    Ограничивает выдачу константой `SKILLS_AUTOCOMPLETE_LIMIT`.

    Returns:
        JSON-список объектов `{"id": int, "name": str}`.
        Параметр `safe=False` необходим, т.к. возвращается list, а не dict.
    """
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.filter(name__istartswith=query).order_by("name")[
        :SKILLS_AUTOCOMPLETE_LIMIT
    ]
    data = [{"id": skill.id, "name": skill.name} for skill in skills]
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def add_skill_view(request, project_id):
    """Добавляет навык к проекту.

    Принимает JSON с `skill_id` или `name`. Если `name` передан,
    создаёт новый навык через `get_or_create`.
    Доступно только владельцу проекта.

    Returns:
        JSON с информацией о навыке и флагами `created`/`added`.
    """
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user:
        return JsonResponse(
            {"status": "error", "detail": "Forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {"status": "error", "detail": "Invalid JSON"},
            status=HTTPStatus.BAD_REQUEST,
        )

    skill_id = body.get("skill_id")
    name = body.get("name", "").strip()

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
        created = False
    elif name:
        skill, created = Skill.objects.get_or_create(name=name)
    else:
        return JsonResponse(
            {"status": "error", "detail": "skill_id or name required"},
            status=HTTPStatus.BAD_REQUEST,
        )

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)

    return JsonResponse(
        {
            "id": skill.id,
            "name": skill.name,
            "created": created,
            "added": added,
        }
    )


@login_required
@require_POST
def remove_skill_view(request, project_id, skill_id):
    """Удаляет навык из проекта.

    Проверяет право владения и наличие навыка у проекта.
    Возвращает 400, если навык не привязан к проекту.
    """
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user:
        return JsonResponse(
            {"status": "error", "detail": "Forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )
    skill = get_object_or_404(Skill, pk=skill_id)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse(
            {"status": "error", "detail": "Skill not in project"},
            status=HTTPStatus.BAD_REQUEST,
        )
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
