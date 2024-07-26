from django.http import JsonResponse
from django.core.management import call_command
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Movie, CinemaShowtime
from .serializers import MovieSerializer, CinemaShowtimeSerializer

import logging
logger = logging.getLogger(__name__)

class UpdateMoviesView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            call_command('update_movies')
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        logger.debug('Received POST request with data: %s', request.data)
        
        if isinstance(request.data, dict):
            logger.debug('Handling single object')
            serializer = MovieSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
            logger.debug('Serializer errors: %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif isinstance(request.data, list):
            logger.debug('Handling list of objects')
            serializer = MovieSerializer(data=request.data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
            logger.debug('Serializer errors: %s', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        logger.debug('Invalid data format: %s', request.data)
        return Response({'status': 'error', 'message': 'Invalid data format'}, status=status.HTTP_400_BAD_REQUEST)
        
class UpdateShowtimesView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            call_command('update_showtimes')
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateAllView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            call_command('update_movies')
            call_command('update_showtimes')
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
