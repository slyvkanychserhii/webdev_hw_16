from django.contrib import admin
from .helpers import end_of_month
from .models import Category, Task, SubTask


def update_deadline(modeladmin, request, queryset):
    queryset.update(deadline=end_of_month())


update_deadline.short_description = "Move the deadline to the end of the month"


@admin.register(Category)
class CategoryModelAdmin(admin.ModelAdmin):
    pass


class TaskCategoryInline(admin.TabularInline):
    '''
    Используется для отображения связанных объектов в табличном формате.
    https://docs.djangoproject.com/en/dev/ref/contrib/admin/#working-with-many-to-many-models
    '''
    model = Task.categories.through
    extra = 1  # Определяет количество пустых форм для ввода новых объектов.


class TaskSubTaskInline(admin.StackedInline):
    '''
    Используется для отображения связанных объектов в вертикальном формате
    '''
    model = SubTask
    extra = 1  # Определяет количество пустых форм для ввода новых объектов.


@admin.register(Task)
class TaskModelAdmin(admin.ModelAdmin):
    # list settings
    list_display = ('title', 'description', 'status', 'created_at', 'deadline')
    search_fields = ('title', 'description')
    list_filter = ('status', 'created_at', 'deadline')
    ordering = ('deadline', 'title')
    list_per_page = 3
    actions = [update_deadline]

    # item settings
    # fields = ('title', 'description', 'status', 'deadline')
    exclude = ['created_at', 'categories']
    inlines = [TaskCategoryInline, TaskSubTaskInline]


@admin.register(SubTask)
class SubTaskModelAdmin(admin.ModelAdmin):
    # list settings
    list_display = ('title', 'description', 'status', 'created_at', 'deadline')
    search_fields = ('title', 'description')
    list_filter = ('status', 'created_at', 'deadline')
    ordering = ('deadline', 'title')
    list_per_page = 3
    actions = [update_deadline]

    # item settings
    exclude = ['created_at']
