from django import forms


def validate_github_url(url):
    """Валидация ссылки на GitHub.

    Args:
        url: Ссылка для проверки.

    Returns:
        Проверенную ссылку.

    Raises:
        ValidationError: Если ссылка не ведет на github.com.
    """

    if url and "github.com" not in url:
        raise forms.ValidationError("Ссылка должна вести на GitHub")
    return url
