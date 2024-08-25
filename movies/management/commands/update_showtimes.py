import datetime
from django.core.management.base import BaseCommand
from movies.models import Movie
from movies.scraping.cinecolombia_scraper import CineColombiaScraper
from movies.scraping.cinepolis_scraper import CinepolisScraper
from movies.scraping.cinemark_scraper import CineMarkScraper
from movies.scraping.izimovie_scraper import IziMovieScraper
from movies.scraping.royalfilms_scraper import RoyalFilmsScraper
from movies.serializers import CinemaShowtimeSerializer
from django.db import transaction
from django.conf import settings
import requests
import json
from datetime import date


class Command(BaseCommand):
    help = "Actualiza los datos de funciones de las películas utilizando web scraping"

    def handle(self, *args, **kwargs):
        scrapers = [CineColombiaScraper(), CinepolisScraper(), CineMarkScraper(), IziMovieScraper(), RoyalFilmsScraper()]

        all_showtimes = []

        for scraper in scrapers:
            try:
                cinema_name = scraper.get_cinema_name()
                cinema_showtimes = self.get_showtimes(scraper, cinema_name)
                if cinema_showtimes:
                    # Asignar la ID de la película correspondiente a cada función
                    for showtime in cinema_showtimes:
                        showtime_with_id = self.add_movie_id(showtime)
                        if showtime_with_id:
                            all_showtimes.append(showtime_with_id)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al procesar {scraper.__class__.__name__}: {str(e)}"
                    )
                )
        # Convertir las fechas a cadenas
        self.convert_dates_to_str(all_showtimes)
        # Enviar los datos recolectados a la API después del scraping
        self.send_data_to_api(all_showtimes)

    def get_showtimes(
        self, cinema_scraper: object, cinema_name: str
    ) -> list[dict] | None:
        try:
            cinema_showtimes = cinema_scraper.get_showtimes()
            return cinema_showtimes

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error al hacer el scraping de {cinema_name}: {e}")
            )
            return None

    def add_movie_id(self, showtime: dict) -> dict | None:
        # Buscar la primera película que coincida con el título
        movie = Movie.objects.filter(
            title=showtime["title"], cinema_name=showtime["cinema_name"]
        ).first()

        if movie is None:
            self.stdout.write(
                self.style.ERROR(f"Película '{showtime['title']}' no encontrada")
            )
            return None

        showtime["movie"] = movie.id
        return showtime

    def convert_dates_to_str(self, data):
        """Convierte fechas en un diccionario a cadenas en formato YYYY-MM-DD"""
        if isinstance(data, list):
            for item in data:
                self.convert_dates_to_str(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, date):
                    data[key] = (
                        value.isoformat()
                    )  # Convierte la fecha a formato YYYY-MM-DD
                elif isinstance(value, dict) or isinstance(value, list):
                    self.convert_dates_to_str(value)

    def send_data_to_api(self, showtimes: list[dict]) -> None:
        post_url = "https://api-calinema.onrender.com/api/create_movies/"

        # Enviar los datos a la API
        try:
            response = requests.post(post_url, json=showtimes)

            if response.status_code == 201:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Funciones de películas enviadas correctamente a la API."
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al enviar datos: {response.status_code} {response.text}"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error al enviar datos a la API: {str(e)}")
            )
