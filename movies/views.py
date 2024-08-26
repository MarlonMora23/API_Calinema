from django.http import JsonResponse
from django.core.management import call_command
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Movie, CinemaShowtime
from .serializers import MovieSerializer, CinemaShowtimeSerializer
from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.generics import GenericAPIView


# Vistas para ejecutar el scraping
class UpdateMoviesView(APIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get(self, request, *args, **kwargs):
        try:
            call_command("update_movies")
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateShowtimesView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            call_command("update_showtimes")
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Vistas para recibir y guardar películas y funciones en la base de datos
class CreateMoviesView(APIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def post(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = MovieSerializer(data=request.data, many=True)
        else:
            serializer = MovieSerializer(data=[request.data], many=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateShowtimesView(APIView):
    queryset = CinemaShowtime.objects.all()
    serializer_class = CinemaShowtimeSerializer

    def post(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = CinemaShowtimeSerializer(data=request.data, many=True)
        else:
            serializer = CinemaShowtimeSerializer(data=[request.data], many=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
