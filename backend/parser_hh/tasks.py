from celery import shared_task
from .utils import DataParsing, SendFeedbackToTheJob
from .models import JobVacancy


@shared_task()
def start_parser():
    print('start parser hh.ru')
    search_text_list = ['python', 'django rest framework', 'django', 'fastapi', 'celery']

    parser = DataParsing()
    parser.search_text_list = search_text_list
    parser.run()


@shared_task()
def start_bot():
    print('start bot hh.ru')
    vacancy_list = JobVacancy.objects.filter(responded=False)

    bot = SendFeedbackToTheJob()
    bot.vacancies = vacancy_list
    bot.run()