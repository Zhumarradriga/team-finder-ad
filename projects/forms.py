from django import forms

from projects.models import Project


class ProjectForm(forms.ModelForm):
    """Форма для создания и редактирования проектов.

    Attributes:
        status: Поле выбора статуса с фиксированным набором вариантов.
    """

    status = forms.ChoiceField(
        choices=Project.Status,
        label="Статус",
    )

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
            "status": "Статус проекта",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
