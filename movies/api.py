from .models import Movie, CinemaShowtime
from rest_framework import viewsets, permissions
from .serializers import MovieSerializer, CinemaShowtimeSerializer

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = MovieSerializer

class CinemaShowtimeViewSet(viewsets.ModelViewSet):
    queryset = CinemaShowtime.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = CinemaShowtimeSerializer