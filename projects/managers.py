from django.db import models


class ProjectManager(models.Manager):
    def open(self):
        """Все открытые проекты, готовые к участию."""
        return self.filter(status=self.model.Status.OPEN)

    def closed(self):
        """Все завершённые проекты."""
        return self.filter(status=self.model.Status.OPEN)

    def by_owner(self, user):
        """Проекты, созданные конкретным пользователем."""
        return self.filter(owner=user)

    def with_participant(self, user):
        """Проекты, в которых пользователь участвует (включая свои)."""
        return self.filter(
            models.Q(owner=user) | models.Q(participants=user)
        ).distinct()
