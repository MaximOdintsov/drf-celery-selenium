from django.urls import path
from .views import RunParserView, RunBotView


urlpatterns = [
    path('run-parser/', RunParserView.as_view(), name='run_parser'),
    path('run-bot/', RunBotView.as_view(), name='run_bot'),
]