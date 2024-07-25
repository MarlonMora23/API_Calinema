import datetime
from django.core.management.base import BaseCommand
from movies.models import Movie
from movies.scraping.cinecolombia_scraper import CineColombiaScraper
from movies.scraping.cinepolis_scraper import CinepolisScraper
from movies.scraping.cinemark_scraper import CineMarkScraper
from movies.scraping.izimovie_scraper import IziMovieScraper
from movies.scraping.royalfilms_scraper import RoyalFilmsScraper
from movies.serializers import CinemaShowtimeSerializer


class Command(BaseCommand):
    help = "Actualiza los datos de funciones de las peliculas utilizando web scraping"

    def handle(self, *args, **kwargs):
        scrapers = [
            CineColombiaScraper(),
            CinepolisScraper(),
            CineMarkScraper(),
            IziMovieScraper(),
            RoyalFilmsScraper(),
            IziMovieScraper(),
        ]

        for scraper in scrapers:
            cinema_name = scraper.get_cinema_name()
            cinema_showtimes = self.get_showtimes(scraper, cinema_name)
            self.process_showtimes(cinema_showtimes, cinema_name)

    # Validar que existan funciones de las peliculas y guardarlas
    def process_showtimes(
        self, cinema_showtimes: list[dict], cinema_name: str
    ) -> list[dict]:
        if self.has_showtimes(cinema_showtimes, cinema_name):
            self.serialize_showtimes(cinema_showtimes, cinema_name)

    # Ejecutar el web scraping para obtener las funciones de las peliculas
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

    def validate_showtimes(
        self, showtimes: list[dict], cinema_name: str
    ) -> list[CinemaShowtimeSerializer]:
        valid_showtimes = []

        for showtime in showtimes:
            showtime = self.add_movie_id(showtime)

            if showtime is None:
                continue

            serializer = CinemaShowtimeSerializer(data=showtime)

            if serializer.is_valid():
                valid_showtimes.append(serializer)

            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error en los datos del showtime de {cinema_name}: {serializer.errors}"
                    )
                )

        return valid_showtimes

    def serialize_showtimes(self, showtimes: list[dict], cinema_name: str) -> None:
        valid_showtimes = self.validate_showtimes(showtimes, cinema_name)

        if valid_showtimes:
            for serializer in valid_showtimes:
                serializer.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Funciones de peliculas de {cinema_name} actualizadas y guardados correctamente en la base de datos y en la API REST."
                )
            )

    def has_showtimes(
        self, showtimes: list[dict] | None, cinema_name: str = ""
    ) -> bool:
        if not showtimes or len(showtimes) == 0:
            self.stdout.write(
                self.style.ERROR(
                    f"Error al hacer el scraping de {cinema_name}. No se encontraron películas."
                )
            )
            return False

        return True
