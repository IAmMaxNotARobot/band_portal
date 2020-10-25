from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from loguru import logger

from .serializers import *
from .models import *
from tid_portal import settings

logger.add(settings.BASE_DIR + "/debug.log", format="{time} {level} {message}", rotation="2 week", compression="zip")


@logger.catch
@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def rest_get_live_list(request):
    """ Return live list in json format """


    song_queryset = Song.objects.filter(live_position__gt=0).order_by('live_position')
    if request.method == "GET":
        song_data = SongSerializer(song_queryset, many=True).data
        return Response({"data": song_data}, status=status.HTTP_200_OK)

