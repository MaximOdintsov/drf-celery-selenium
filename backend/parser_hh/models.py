from django.db import models


class JobVacancy(models.Model):
    vacancy_name = models.CharField('Vacancy name', max_length=255)
    vacancy_link = models.CharField('Vacancy link', max_length=255, primary_key=True)
    company_name = models.CharField('Company name', max_length=255, null=True, blank=True)
    company_link = models.CharField('Company link', max_length=255, null=True, blank=True)
    responded = models.BooleanField('Responded to a vacancy', default=False)

    class Meta:
        verbose_name = 'Job vacancy'
        verbose_name_plural = 'Job vacancies'

    def __str__(self):
        return f'{self.company_name} - {self.vacancy_name}'