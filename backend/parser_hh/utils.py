import pickle
import random
import time

import requests
import fake_useragent
from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver.common.by import By

from .models import JobVacancy
import celery

class DataParsing:
    """
    Collects data from hh.ru, validation and returns it
    """

    def __init__(self):
        self.user_agent = fake_useragent.UserAgent()

    def get_page_count(self, text):
        """
        Counts the number of pages
        """
        data = requests.get(
            url=f'https://hh.ru/search/vacancy?search_field=name&search_field=company_name&search_field=description&enable_snippets=true&text={text}&page=1',
            headers={'user-agent': self.user_agent.random},
        )
        if data.status_code != 200:
            return Response(status.HTTP_400_BAD_REQUEST)

        soup = BeautifulSoup(data.content, 'lxml')

        try:
            page_count = int(soup.find('div', attrs={'class': 'pager'}).find_all('span', recursive=False)[-1].find('a').find('span').text)
            return page_count
        except Exception:
            return Response(status.HTTP_400_BAD_REQUEST)

    def get_content_from_page(self, text, page):
        """
        Parses all data from the page
        """
        data = requests.get(
            url=f'https://hh.ru/search/vacancy?search_field=name&search_field=company_name&search_field=description&enable_snippets=true&text={text}&page={page}',
            headers={'user-agent': self.user_agent.random},
        )
        if data.status_code != 200:
            return Response(status.HTTP_400_BAD_REQUEST)

        soup = BeautifulSoup(data.content, 'lxml')
        return soup

    def get_vacancy_data(self, search_text_list):
        """
        Processes data received from a get_content_from_page
        Returns a generator
        """
        for text in search_text_list:
            pages = self.get_page_count(text=text)

            for page in range(pages):
                try:
                    data = self.get_content_from_page(text=text, page=page)
                    vacancies = data.find_all('div', attrs={'class': 'vacancy-serp-item-body__main-info'})

                    for vacancy in vacancies:
                        vacancy_link = vacancy.find('a', attrs={'class': 'serp-item__title'}).attrs['href'].split('?')[0]
                        vacancy_name = vacancy.find('a', attrs={'class': 'serp-item__title'}).string.lower()
                        company_link = f"https://hh.ru{vacancy.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).attrs['href'].split('?')[0]}"
                        company_name = vacancy.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).stripped_strings

                        if len(JobVacancy.objects.filter(vacancy_link=vacancy_link)) == 0:
                            for text in ['python', 'django, drf', 'fastapi', 'flask']:
                                if text in vacancy_name:
                                    for string in company_name:
                                        company_name = string.lower()

                                    data_list = [vacancy_name, vacancy_link, company_name, company_link]
                                    yield data_list
                                    break
                        continue

                except Exception:
                    continue
                time.sleep(random.randrange(1, 2))


class SendFeedbackToTheJob:
    def __init__(self):
        self.webdriver = webdriver.Chrome()
        self.webdriver.get('https://hh.ru/')
        for cookie in pickle.load(open('parser_hh/cookies', 'rb')):
            self.webdriver.add_cookie(cookie)

        time.sleep(random.randrange(3, 5))
        self.webdriver.refresh()

    @staticmethod
    def get_covering_letter(vacancy_name):
        context = {'vacancy_name': vacancy_name}
        letter = render_to_string('parser_hh/covering_letter.html',
                                  context=context)
        return letter

    def check_if_a_job_has_already_been_applied_for(self, url, vacancy):
        try:
            self.webdriver.get(url)
            time.sleep(random.randrange(1, 3))
            element = self.webdriver.find_element(By.CSS_SELECTOR, 'a[data-qa="vacancy-response-link-top"]')
            url_for_response = element.get_attribute('href')
            if 'vacancy_response' in url_for_response:
                return url_for_response
            else:
                vacancy.responded = True
                vacancy.save()
                return False

        except Exception:
            vacancy.responded = True
            vacancy.save()
            return False

    def send_resume_and_cover_letter(self, vacancies):
        for vacancy in vacancies:
            try:
                url = vacancy.vacancy_link
                time.sleep(random.randrange(2, 4))
                url_for_response = self.check_if_a_job_has_already_been_applied_for(url, vacancy)
                if url_for_response:
                    self.webdriver.get(url_for_response)
                    time.sleep(random.randrange(2, 4))

                    try:
                        # clicks on "Send Anyway" if the job is in another country
                        self.webdriver.find_element(
                            By.CSS_SELECTOR, 'a[data-qa="vacancy-response-link-top"]'
                        ).click()
                        time.sleep(random.randrange(2, 4))
                    except Exception:
                        pass

                    try:
                        # clicks to send a response to the vacancy
                        self.webdriver.find_element(
                            By.CSS_SELECTOR, 'button[data-qa="relocation-warning-confirm"]'
                        ).click()
                        time.sleep(random.randrange(2, 4))
                    except Exception:
                        pass

                    # clicks to write a cover letter
                    self.webdriver.find_element(
                        By.CSS_SELECTOR, 'button[data-qa="vacancy-response-letter-toggle"]',
                    ).click()
                    time.sleep(random.randrange(2, 4))

                    # writes a cover letter
                    self.webdriver.find_element(
                        By.CSS_SELECTOR, '.bloko-textarea'
                    ).send_keys(self.get_covering_letter(vacancy.vacancy_name))
                    time.sleep(random.randrange(2, 4))

                    # sends a cover letter
                    self.webdriver.find_element(
                        By.CSS_SELECTOR, 'button[data-qa="vacancy-response-letter-submit"]'
                    ).click()

                    vacancy.responded = True
                    vacancy.save()

            except Exception:
                vacancy.responded = True
                vacancy.save()
