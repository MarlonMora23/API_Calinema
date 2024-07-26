from django.core.management.base import BaseCommand
from movies.scraping.cinecolombia_scraper import CineColombiaScraper
from movies.scraping.cinepolis_scraper import CinepolisScraper
from movies.scraping.cinemark_scraper import CineMarkScraper
from movies.scraping.izimovie_scraper import IziMovieScraper
from movies.scraping.royalfilms_scraper import RoyalFilmsScraper
from movies.serializers import MovieSerializer
from django.db import transaction
import requests


class Command(BaseCommand):
    help = "Actualiza los datos utilizando web scraping"

    def handle(self, *args, **kwargs) -> None:
        scrapers = [CineColombiaScraper()]

        all_movies = []

        for scraper in scrapers:
            try:
                # cinema_name = scraper.get_cinema_name()
                # cinema_movies = scraper.get_movies()
                # self.process_movies(cinema_movies, cinema_name)
                # all_movies.extend(cinema_movies)

                all_movies = [
                    [
                        {
                            "title": "Deadpool & Wolverine",
                            "duration": "127 Minutos",
                            "classification": "Exclusiva para mayores de 15 años",
                            "cinema_name": "CineColombia",
                            "genres": ["Acción", "Ciencia Ficción", "Comedia"],
                            "original_title": "Deadpool & Wolverine",
                            "country_origin": "United States of America",
                            "director": "Shawn Levy",
                            "actors": "Ryan Reynolds, Hugh Jackman, Emma Corrin, Morena Baccarin, Rob Delaney, Karan Soni, Matthew Macfadyen",
                            "language": "Inglés",
                            "synopsis": "Wolverine se recupera de sus heridas cuando cruza su camino con Deadpool, quien ha viajado en el tiempo para curarlo con la esperanza de hacerse amigos y formar un equipo para acabar con un enemigo común.",
                            "image_url": "https://archivos-cms.cinecolombia.com/images/_aliases/poster_card/2/7/0/1/61072-1-esl-CO/8024c9dd9aab-480x670_cine_colombia.png",
                        },
                        {
                            "title": "Immaculate",
                            "duration": "89 Minutos",
                            "classification": "Exclusiva para mayores de 15 años",
                            "cinema_name": "CineColombia",
                            "genres": ["Terror"],
                            "original_title": "Immaculate",
                            "country_origin": "Italy, United States of America",
                            "director": "Michael Mohan",
                            "actors": "Sydney Sweeney, Álvaro Morte, Simona Tabasco",
                            "language": "Inglés e Italiano",
                            "synopsis": "Cecilia (Sydney Sweeney), una monja fervientemente devota, se aventura hacia un remoto convento en la campiña italiana en busca de la consagración espiritual. Sin embargo, lo que inicialmente prometía ser un encuentro espiritual se transforma en una oscura y aterradora pesadilla. A medida que explora los pasillos y los rincones ocultos del convento, Cecilia descubre secretos siniestros y horrores indescriptibles que desafían toda lógica y razón.",
                            "image_url": "https://archivos-cms.cinecolombia.com/images/_aliases/poster_card/4/2/5/8/58524-1-esl-CO/0dd37614f755-imct_cineco_pstr-dskp_480x670.png",
                        },
                    ]
                ]
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error al procesar {scraper.__class__.__name__}: {str(e)}"
                    )
                )

        # Enviar los datos recolectados a la API después del scraping
        self.send_data_to_api(all_movies)

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

    def send_data_to_api(self, movies: list[dict]) -> None:
        post_url = "https://api-calinema.onrender.com/api/movies/"

        # # Headers (opcional)
        # headers = {
        #     'Content-Type': 'application/json',
        #     'Authorization': 'Bearer tu_token_de_autenticacion'  # si es necesario
        # }

        # # Construir el payload en el formato correcto
        # payload = {"movies": movies}

        # Realiza la petición POST
        try:
            response = requests.post(post_url, json=movies)

            # Verifica la respuesta de la petición POST
            if response.status_code == 201:  # Código de estado para creación exitosa
                self.stdout.write(
                    self.style.SUCCESS("Datos enviados correctamente a la API.")
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
