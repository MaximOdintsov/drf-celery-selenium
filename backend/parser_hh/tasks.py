from typing import List

from celery import shared_task

from .models import JobVacancy
from .utils import DataParsing, SendFeedbackToTheJob


@shared_task()
def set_data_to_database(search_text_list: List[None]):
    parsing = DataParsing()

    vacancies = parsing.get_vacancy_data(search_text_list=search_text_list)
    for data_list in vacancies:
        JobVacancy.objects.create(
            vacancy_name=data_list[0],
            vacancy_link=data_list[1],
            company_name=data_list[2],
            company_link=data_list[3],
        )


@shared_task()
def send_feedback_to_the_job():
    bot = SendFeedbackToTheJob()

    vacancies = JobVacancy.objects.filter(responded=False)[:40]
    bot.send_resume_and_cover_letter(vacancies=vacancies)
