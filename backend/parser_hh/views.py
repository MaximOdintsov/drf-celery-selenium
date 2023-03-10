from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import start_parser, start_bot


class RunParserView(APIView):

    def post(self, request):
        start_parser.delay()
        return Response({'message': 'All ok, celery is working'})


class RunBotView(APIView):

    def post(self, request):
        start_bot.delay()
        return Response({'message': 'All ok, celery is working'})
