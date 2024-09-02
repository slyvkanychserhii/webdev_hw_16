from django.db import models
from django.db.models.functions import Lower
from .helpers import end_of_month


class StatusType(models.IntegerChoices):
    NEW = 1, "New"
    IN_PROGRESS = 2, "In progress"
    PENDING = 3, "Pending"
    BLOCKED = 4, "Blocked"
    DONE = 5, "Done"


class Category(models.Model):
    name = models.CharField(
        verbose_name='category name',
        max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        constraints = [
            models.UniqueConstraint(Lower('name'), name='unique_lower_name')
        ]


class Task(models.Model):
    title = models.CharField(
        verbose_name='task name',
        max_length=100)
    description = models.TextField(
        verbose_name='task description',
        blank=True,
        null=True)
    status = models.IntegerField(
        verbose_name='task status',
        choices=StatusType.choices,
        default=StatusType.NEW)
    deadline = models.DateTimeField(
        verbose_name='deadline date and time',
        default=end_of_month)
    created_at = models.DateTimeField(
        verbose_name='creation date and time',
        auto_now_add=True)
    categories = models.ManyToManyField(
        to=Category,
        related_name='tasks',
        related_query_name='tasks',
        verbose_name='task categories',
        blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = '"my_app_task"'
        verbose_name = 'task'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                Lower('title'),
                name='%(app_label)s_%(class)s_name_lower_unique')
        ]


class SubTask(models.Model):
    title = models.CharField(
        verbose_name='subtask name',
        max_length=100)
    description = models.TextField(
        verbose_name='subtask description',
        blank=True, null=True)
    status = models.IntegerField(
        verbose_name='subtask status',
        choices=StatusType.choices,
        default=StatusType.NEW)
    deadline = models.DateTimeField(
        verbose_name='deadline date and time',
        default=end_of_month)
    created_at = models.DateTimeField(
        verbose_name='creation date and time',
        auto_now_add=True)
    task = models.ForeignKey(
        to=Task, on_delete=models.CASCADE,
        related_name='subtasks',
        related_query_name='subtask',
        verbose_name='main task')

    def __str__(self):
        return self.title

    class Meta:
        db_table = '"my_app_subtask"'
        verbose_name = 'subtask'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                Lower('title'),
                name='%(app_label)s_%(class)s_name_lower_unique')
        ]
