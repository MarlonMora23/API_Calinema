from django.core.management.base import BaseCommand
from movies.scraping.cinecolombia_scraper import CineColombiaScraper
from movies.scraping.cinepolis_scraper import CinepolisScraper
from movies.scraping.cinemark_scraper import CineMarkScraper
from movies.scraping.izimovie_scraper import IziMovieScraper
from movies.scraping.royalfilms_scraper import RoyalFilmsScraper
from movies.serializers import MovieSerializer
from django.db import transaction


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

        for scraper in scrapers:
            try:
                cinema_name = scraper.get_cinema_name()
                cinema_movies = scraper.get_movies()
                self.process_movies(cinema_movies, cinema_name)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al procesar {scraper.__class__.__name__}: {str(e)}"
                    )
                )

    # Validar que existan las peliculas y guardarlas
    def process_movies(self, cinema_movies: list[dict], cinema_name: str = "") -> None:
        if self.has_movies(cinema_movies, cinema_name):
            self.serialize_movies(cinema_movies, cinema_name)

    def validate_movies(self, movies: list[dict]) -> list[MovieSerializer]:
        valid_movies = []
        for movie in movies:
            serializer = MovieSerializer(data=movie)
            if serializer.is_valid():
                valid_movies.append(serializer)
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Error al serializar la película: " + str(serializer.errors)
                    )
                )

        return valid_movies

    def serialize_movies(self, movies: list[dict], cinema_name: str = "") -> dict:
        valid_movies = self.validate_movies(movies)

        if valid_movies:
            try:
                with transaction.atomic():
                    for serializer in valid_movies:
                        serializer.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Películas de {cinema_name} actualizadas y guardadas correctamente en la base de datos y en la API REST."
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error al guardar las películas: {str(e)}")
                )

    def has_movies(self, movies: list[dict] | None, cinema_name: str = "") -> bool:
        if not movies or len(movies) == 0:
            self.stdout.write(
                self.style.ERROR(
                    f"Error al hacer el scraping de {cinema_name}. No se encontraron películas."
                )
            )
            return False

        return True
