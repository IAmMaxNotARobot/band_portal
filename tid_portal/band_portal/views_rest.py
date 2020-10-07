#from api.serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .models import *
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from loguru import logger

logger.add("models_debug.log", format="{time} {level} {message}", rotation="2 week", compression="zip")


@logger.catch
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rest_get_live_list(request):
    song_queryset = Song.objects.filter(live_position__gt=0).order_by('live_position')
    if request.method == "GET":
        song_data = SongSerializer(song_queryset, many=True).data
        return Response({"data": song_data}, status=status.HTTP_200_OK)


"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_markets(request):
    market_queryset = Market.objects.all()



    if request.method == "GET":
        market_data = MarketSerializer(market_queryset, many=True).data
        return Response({"data": market_data}, status=status.HTTP_200_OK)

http://iammaxnotarobot.pythonanywhere.com/library/section_Django/
http://iammaxnotarobot.pythonanywhere.com/library/article_10/
"""