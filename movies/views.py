from django.http import JsonResponse
from django.core.management import call_command
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class UpdateMoviesView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            call_command('update_movies')
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
        
