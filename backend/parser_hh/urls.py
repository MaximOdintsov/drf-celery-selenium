from django.urls import path
from .views import RunParserView, RunBotView


urlpatterns = [
    path('run-hh-parser', RunParserView.as_view(), name='run_hh_parser'),
    path('run-hh-bot', RunBotView.as_view(), name='run_hh_bot'),
]