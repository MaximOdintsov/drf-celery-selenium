from django.contrib import admin

from .models import JobVacancy


@admin.register(JobVacancy)
class BaseTaskAdmin(admin.ModelAdmin):
    list_display = ['vacancy_name', 'vacancy_link', 'company_name', 'company_link', 'create', 'responded']
    list_filter = ['responded']
