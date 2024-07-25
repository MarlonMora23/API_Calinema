from bs4 import BeautifulSoup
from movies.scraping.scraper import (
    Scraper,
    SeleniumMoviesScraper,
    SeleniumShowtimesScraper,
    BeautifulSoupMoviesScraper,
)
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import datetime


class CinepolisScraper(Scraper):
    def __init__(self) -> None:
        super().__init__()
        self.cinema_name = "Cinepolis"
        self.url = "https://cinepolis.com.co/cartelera/cali-colombia"
        self.movies_scraper = CinepolisMoviesScraper(self.cinema_name, self.url)
        self.showtimes_scraper = CinepolisShowtimesScraper(self.cinema_name, self.url)


class CinepolisMoviesScraper(SeleniumMoviesScraper, BeautifulSoupMoviesScraper):
    def __init__(self, cinema_name: str, url: str) -> None:
        SeleniumMoviesScraper.__init__(self)
        BeautifulSoupMoviesScraper.__init__(self)
        self.cinema_name = cinema_name
        self.url = url

    def scrape_movies(self) -> list[dict] | None:
        raw_movies = []
        movies_set = set()
        movies_data = self.selenium_driver.wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "tituloPelicula"))
        )

        for movie_element in tqdm(
            movies_data, desc="Scraping Cinepolis movies", unit="movie"
        ):
            try:
                raw_movie = self.get_raw_movies(movie_element, movies_set)

                if raw_movie:
                    raw_movies.append(raw_movie)

            except NoSuchElementException:
                continue

        if not raw_movies:
            print("No se encontraron datos de las peliculas")
            return None

        return raw_movies

    def format_movie(self, raw_movie: dict) -> dict | None:
        formatted_movie = {
            "title": raw_movie["title"],
            "duration": raw_movie["duration"],
            "classification": self.format_classification(raw_movie["classification"]),
            "cinema_name": raw_movie["cinema_name"],
            "genres": self.format_genres(raw_movie["genres"]),
            "original_title": raw_movie["original_title"],
            "country_origin": raw_movie["country_origin"],
            "director": raw_movie["director"],
            "actors": self.format_actors(raw_movie["actors"]),
            "language": raw_movie["language"],
            "synopsis": raw_movie["synopsis"],
            "image_url": raw_movie["image_url"],
        }

        return formatted_movie

    def get_raw_movies(self, movie_element: WebElement, movies_set: set) -> dict | None:
        movies = {}

        # Obtener los datos
        title = movie_element.find_element(
            By.CLASS_NAME, "datalayer-movie"
        ).text.strip()
        duration = movie_element.find_element(By.CLASS_NAME, "duracion").text.strip()
        classification = movie_element.find_element(
            By.CLASS_NAME, "clasificacion"
        ).text.strip()
        movie_details = movie_element.find_element(By.CLASS_NAME, "data-layer")
        genres = movie_details.get_attribute("data-genero")
        director = movie_details.get_attribute("data-director")
        actors = movie_details.get_attribute("data-actor")
        original_title = movie_details.get_attribute("data-titulooriginal")
        image_url = movie_element.find_element(By.TAG_NAME, "img").get_attribute("src")
        synopsis_element = movie_element.find_element(By.CLASS_NAME, "datalayer-movie")
        element_id = synopsis_element.get_attribute("id")

        # Obtener el url donde está la sinopsis
        synopsis_url = None
        synopsis = ""

        if "cinepolis-limonar-cali" in element_id:
            synopsis_url = element_id.split("cinepolis-limonar-cali-")[-1].strip()

        elif "cinepolis-vip-limonar-cali" in element_id:
            synopsis_url = element_id.split("cinepolis-vip-limonar-cali-")[-1].strip()

        if synopsis_url:
            synopsis = self.get_synopsis(
                f"https://cinepolis.com.co/pelicula/{synopsis_url}"
            )

        if title in movies_set:
            return None

        movies_set.add(title)

        movies["title"] = title
        movies["cinema_name"] = self.cinema_name
        movies["genres"] = genres
        movies["classification"] = classification
        movies["duration"] = duration
        movies["image_url"] = image_url
        movies["synopsis"] = synopsis
        movies["original_title"] = original_title
        movies["country_origin"] = ""
        movies["director"] = director
        movies["actors"] = actors
        movies["language"] = ""

        return movies

    def format_duration(self, duration: str) -> str:
        return duration.title() + 'utos'
    
    def format_classification(self, classification: str) -> str:
        if classification == "TP":
            classification = "Para todo el público"

        elif classification == "A7":
            classification = "Exclusiva para mayores de 7 años"

        elif classification == "A12":
            classification = "Exclusiva para mayores de 12 años"

        elif classification == "A15":
            classification = "Exclusiva para mayores de 15 años"

        elif classification == "A18":
            classification = "Exclusiva para mayores de 18 años"

        return classification

    def get_synopsis(self, url: str) -> str:
        response = self.bs_driver.get_http_response(url)
        if response:
            soup = BeautifulSoup(response.text, "html.parser")
            synopsis = soup.find(
                "p", id="ContentPlaceHolder1_ctl_sinopsis_ctl_sinopsis"
            )

            if not synopsis:
                return ""

            return synopsis.text

    def format_actors(self, actors: str):
        actors = ", ".join(
            actors.replace('"', "").replace("[", "").replace("]", "").split(", ")
        )

        return actors

    def format_genres(self, genres: str):
        return genres.capitalize()


class CinepolisShowtimesScraper(SeleniumShowtimesScraper):
    def __init__(self, cinema_name: str, url: str) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_showtimes(self) -> list[dict] | None:
        raw_showtimes = []

        movies = self.selenium_driver.wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "tituloPelicula"))
        )

        for movie in tqdm(movies, desc="Scraping Cinepolis showtimes", unit="showtime"):
            try:
                movie_raw_showtimes = self.get_raw_showtimes(movie)

                if movie_raw_showtimes:
                    raw_showtimes.extend(movie_raw_showtimes)

            except NoSuchElementException:
                continue

        if not raw_showtimes:
            print("No se encontraron funciones de Cinepolis")
            return None

        return raw_showtimes

    def format_showtime(self, raw_showtime: dict) -> dict | None:
        if (
            raw_showtime["title"] != ""
            and raw_showtime["room"] != ""
            and raw_showtime["format"] != ""
            and raw_showtime["schedule"] != ""
            and raw_showtime["url"] != ""
        ):
            formatted_showtime = {
                "title": raw_showtime["title"],
                "cinema_name": raw_showtime["cinema_name"],
                "room": raw_showtime["room"],
                "format": self.format_movie_format(raw_showtime["format"]),
                "date": self.format_date(),
                "schedule": self.format_schedule(raw_showtime["schedule"]),
                "url": raw_showtime["url"],
            }

            return formatted_showtime

        return None

    def get_raw_showtimes(self, movie: WebElement) -> list[dict]:
        showtimes = []
        title = movie.find_element(By.CLASS_NAME, "datalayer-movie").text.strip()
        room = "Limonar"
        url_element = movie.find_element(By.CLASS_NAME, "datalayer-movie")
        element_id = url_element.get_attribute("id")

        url_movie = ""

        if "cinepolis-limonar-cali" in element_id:
            url_movie = element_id.split("cinepolis-limonar-cali-")[-1].strip()

        elif "cinepolis-vip-limonar-cali" in element_id:
            url_movie = element_id.split("cinepolis-vip-limonar-cali-")[-1].strip()
            room = "VIP Limonar"

        url = f"https://cinepolis.com.co/pelicula/{url_movie}"

        schedules_container = movie.find_elements(By.CLASS_NAME, "horarioExp")

        for format_element in tqdm(schedules_container, leave=False):
            movie_format = format_element.find_element(
                By.CLASS_NAME, "col3.cf.ng-binding"
            ).text
            schedules_element = format_element.find_elements(
                By.CLASS_NAME, "btnhorario"
            )

            schedules_text = [horario.text for horario in schedules_element]

            for schedule in schedules_text:
                showtimes_data = {
                    "title": title,
                    "cinema_name": self.cinema_name,
                    "room": room,
                    "format": movie_format,
                    "date": "",
                    "schedule": schedule,
                    "url": url,
                }

                showtimes.append(showtimes_data)

        return showtimes

    def format_movie_format(self, format: str) -> str:
        return format.replace("\n", " ").title()

    def format_date(self):
        return datetime.date.today()

    def format_schedule(self, schedule: str) -> str | None:
        schedule.replace(
            "\n",
            " ",
        ).strip()

        return schedule
