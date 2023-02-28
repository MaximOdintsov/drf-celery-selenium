

# from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import set_data_to_database, send_feedback_to_the_job

from .models import JobVacancy
from .utils import DataParsing, SendFeedbackToTheJob


class RunParserView(APIView):
    search_text_list = ['python', 'django']

    def post(self, request):
        set_data_to_database(search_text_list=['python', 'django', 'fastapi'])
        return Response({'message': 'all ok, celery is working'})


class RunBotView(APIView):

    def post(self, request):
        send_feedback = send_feedback_to_the_job()
        return Response({'message': 'all ok, celery is working',
                         'send_feedback': send_feedback})