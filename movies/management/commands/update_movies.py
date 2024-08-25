from django.core.management.base import BaseCommand
from movies.scraping.cinecolombia_scraper import CineColombiaScraper
from movies.scraping.cinepolis_scraper import CinepolisScraper
from movies.scraping.cinemark_scraper import CineMarkScraper
from movies.scraping.izimovie_scraper import IziMovieScraper
from movies.scraping.royalfilms_scraper import RoyalFilmsScraper
from movies.serializers import MovieSerializer
from django.db import transaction
from django.conf import settings
import requests


class Command(BaseCommand):
    help = "Actualiza los datos utilizando web scraping"

    def handle(self, *args, **kwargs) -> None:
        scrapers = [
            CineColombiaScraper(),
            CinepolisScraper(),
            CineMarkScraper(),
            IziMovieScraper(),
            RoyalFilmsScraper(),
        ]

        all_movies = []

        for scraper in scrapers:
            try:
                cinema_movies = scraper.get_movies()
                all_movies.extend(cinema_movies)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al procesar {scraper.__class__.__name__}: {str(e)}"
                    )
                )

        # Enviar los datos recolectados a la API después del scraping
        self.send_data_to_api(all_movies)

    def send_data_to_api(self, movies: list[dict]) -> None:
        # Definir la URL según el entorno
        if settings.ENVIRONMENT == "production":
            post_url = "https://api-calinema.onrender.com/api/create_movies/"
        else:
            post_url = "http://127.0.0.1:8000/api/create_movies/"

        # Enviar los datos a la API
        try:
            response = requests.post(post_url, json=movies)

            if response.status_code == 201:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Datos enviados correctamente a la API y guardados en la base de datos."
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al enviar datos a la API: {response.status_code} {response.text}"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error al enviar datos a la API: {str(e)}")
            )
