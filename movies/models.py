from django.db import models
import datetime


class Movie(models.Model):
    title = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    classification = models.CharField(max_length=50)
    cinema_name = models.CharField(max_length=100)
    genres = models.JSONField(blank=True, default=list)
    original_title = models.CharField(max_length=100, blank=True)
    country_origin = models.CharField(max_length=100, blank=True)
    director = models.CharField(max_length=100, blank=True)
    actors = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=100, blank=True)
    synopsis = models.TextField(blank=True)
    image_url = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CinemaShowtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    cinema_name = models.CharField(max_length=100)
    room = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    date = models.DateField(default=datetime.date.today)
    schedule = models.TimeField()
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.movie.title} at {self.schedule} in {self.cinema_name}"
