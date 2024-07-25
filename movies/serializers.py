from rest_framework import serializers
from .models import Movie, CinemaShowtime


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = "__all__"


class CinemaShowtimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaShowtime
        fields = "__all__"
