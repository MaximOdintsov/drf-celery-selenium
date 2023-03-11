import pickle
import random
import time

import requests
import fake_useragent
from my_site.settings import SELENIUM_PATH, PRODUCTION_V
from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By

from .models import JobVacancy


class DataParsing:
    """ Collects data from hh.ru, validation and returns it """

    search_text_list = None

    def __init__(self):
        self.user_agent = fake_useragent.UserAgent()

    def get_page_count(self, text):
        """ Counts the number of pages """

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
        """ Parses all data from the page """

        data = requests.get(
            url=f'https://hh.ru/search/vacancy?search_field=name&search_field=company_name&search_field=description&enable_snippets=true&text={text}&page={page}',
            headers={'user-agent': self.user_agent.random},
        )
        if data.status_code != 200:
            return Response(status.HTTP_400_BAD_REQUEST)

        soup = BeautifulSoup(data.content, 'lxml')
        return soup

    def get_vacancy_data(self):
        """
        Processes data received from a get_content_from_page
        Returns a generator
        """

        relevant_text = ['python', 'django', 'django rest framework', 'drf', 'fastapi', 'flask', 'celery']
        irrelevant_text = ['ml', 'senior', 'lead', 'преподаватель', 'data scien']

        for text in self.search_text_list:
            pages = self.get_page_count(text=text)

            for page in range(pages):
                try:
                    data = self.get_content_from_page(text=text, page=page)
                    vacancies = data.find_all('div', attrs={'class': 'vacancy-serp-item-body__main-info'})

                    for vacancy in vacancies:
                        vacancy_link = vacancy.find('a', attrs={'class': 'serp-item__title'}).attrs['href'].split('?')[0].split('/')[-1]
                        vacancy_name = vacancy.find('a', attrs={'class': 'serp-item__title'}).string
                        company_link = vacancy.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).attrs['href'].split('?')[0].split('/')[-1]
                        company_name = vacancy.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).stripped_strings

                        vacancy_count = len(JobVacancy.objects.filter(vacancy_link=vacancy_link))
                        if vacancy_count == 0:
                            for text_ in irrelevant_text:
                                if text_ in vacancy_name.lower():
                                    raise StopIteration
                            for text_ in relevant_text:
                                if text_ in vacancy_name.lower():
                                    company_name = ' '.join(map(str, company_name))
                                    data_list = [vacancy_name, vacancy_link, company_name, company_link]
                                    yield data_list

                except Exception:
                    continue
                time.sleep(random.randrange(1, 2))

    def set_data_to_database(self):
        for vacancy in self.get_vacancy_data():
            try:
                JobVacancy.objects.create(
                    vacancy_name=vacancy[0],
                    vacancy_link=vacancy[1],
                    company_name=vacancy[2],
                    company_link=vacancy[3],
                )
            except Exception:
                continue

    def run(self):
        self.set_data_to_database()


class SendFeedbackToTheJob:

    vacancies = None

    def __init__(self):
        if PRODUCTION_V:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=800,600')
            # options.add_argument('--disable-gpu')

            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--remote-debugging-port=7900')
            options.add_argument('--remote-debugging-address=0.0.0.0')
            options.set_capability('browserVersion', '110.0')

            self.webdriver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub',
                                              desired_capabilities=options.to_capabilities(),
                                              options=options)
        else:
            self.webdriver = webdriver.Chrome()

        self.webdriver.get('https://hh.ru/')

        try:
            self.load_cookies()
        except Exception:
            self.login_and_dump_cookies()

    def login_and_dump_cookies(self):
        self.webdriver.get('https://hh.ru/account/login')
        time.sleep(60)

    def dump_cookies(self):
        pickle.dump(self.webdriver.get_cookies(), open('parser_hh/cookies.pkl', 'wb'))
        time.sleep(5)

    def load_cookies(self):
        for cookie in pickle.load(open('parser_hh/cookies.pkl', 'rb')):
            self.webdriver.add_cookie(cookie)
        time.sleep(15)
        self.webdriver.refresh()

    @staticmethod
    def get_cover_letter(vacancy_name):
        context = {'vacancy_name': vacancy_name}
        letter = render_to_string('parser_hh/covering_letter.html',
                                  context=context)
        return letter

    @staticmethod
    def make_vacancy_responded_is_true(vacancy):
        vacancy.responded = True
        vacancy.save()

    def check_if_a_job_has_already_been_applied_for(self, url, vacancy):
        try:
            self.webdriver.get(url)
            time.sleep(random.randrange(1, 3))
            element = self.webdriver.find_element(By.CSS_SELECTOR, 'a[data-qa="vacancy-response-link-top"]')
            url_for_response = element.get_attribute('href')
            if 'vacancy_response' in url_for_response:
                return url_for_response
            else:
                self.make_vacancy_responded_is_true(vacancy)
                return False

        except Exception:
            self.make_vacancy_responded_is_true(vacancy)
            return False

    def send_resume_and_cover_letter(self):
        counter = 0
        for vacancy in self.vacancies:
            url = f'https://hh.ru/vacancy/{vacancy.vacancy_link}'
            url_for_response = self.check_if_a_job_has_already_been_applied_for(url, vacancy)

            if counter < 30:
                try:
                    if url_for_response:
                        self.webdriver.get(url_for_response)
                        time.sleep(random.randrange(2, 4))

                        self.job_from_another_country()
                        self.job_response()
                        self.click_cover_letter()
                        self.write_cover_letter(vacancy=vacancy)
                        self.send_cover_letter()

                        counter += 1
                        self.make_vacancy_responded_is_true(vacancy)
                except Exception:
                    self.make_vacancy_responded_is_true(vacancy)
            else:
                self.quit()
                quit()

    def job_from_another_country(self):
        """ Clicks on "Send Anyway" if the job is in another country """

        try:
            self.webdriver.find_element(
                By.CSS_SELECTOR, 'a[data-qa="vacancy-response-link-top"]'
            ).click()
            time.sleep(random.randrange(2, 4))
        except Exception:
            pass

    def job_response(self):
        """ Clicks to send a response to the vacancy """

        try:
            self.webdriver.find_element(
                By.CSS_SELECTOR, 'button[data-qa="relocation-warning-confirm"]'
            ).click()
            time.sleep(random.randrange(2, 4))
        except Exception:
            pass

    def click_cover_letter(self):
        self.webdriver.find_element(
            By.CSS_SELECTOR, 'button[data-qa="vacancy-response-letter-toggle"]',
        ).click()
        time.sleep(random.randrange(2, 4))

    def write_cover_letter(self, vacancy):
        self.webdriver.find_element(
            By.CSS_SELECTOR, '.bloko-textarea'
        ).send_keys(self.get_cover_letter(vacancy.vacancy_name))
        time.sleep(random.randrange(2, 4))

    def send_cover_letter(self):
        self.webdriver.find_element(
            By.CSS_SELECTOR, 'button[data-qa="vacancy-response-letter-submit"]'
        ).click()

    def run(self):
        self.send_resume_and_cover_letter()
        self.quit()

    def quit(self):
        self.webdriver.close()
        self.webdriver.quit()