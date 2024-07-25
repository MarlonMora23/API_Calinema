from bs4 import BeautifulSoup
from bs4.element import Tag
from movies.scraping.scraper import (
    Scraper,
    BeautifulSoupMoviesScraper,
    SeleniumShowtimesScraper,
)
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import datetime
import requests


class CineColombiaScraper(Scraper):
    def __init__(self):
        super().__init__()
        self.cinema_name = "CineColombia"
        self.url = "https://www.cinecolombia.com/cali/cartelera"
        self.movies_scraper = CineColombiaMoviesScraper(self.cinema_name, self.url)
        self.showtimes_scraper = CineColombiaShowtimesScraper(self.cinema_name, self.url)


class CineColombiaMoviesScraper(BeautifulSoupMoviesScraper):
    def __init__(self, cinema_name: str, url: str) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_movies(self, soup: BeautifulSoup) -> list[Tag]:
        movie_items = soup.find_all("a", class_="movie-item")
        movies = []
        movie_titles = set()

        # Recorrer películas y mostrar barra de progreso
        for movie in tqdm(
            movie_items, desc="Scraping CineColombia movies", unit="movie"
        ):
            title = movie.find("h2", class_="movie-item__title").get_text().strip()

            if title not in movie_titles:
                raw_movies = self.get_raw_movies(movie, title)
                raw_movies_details = self.get_raw_movies_details(movie)

                if not raw_movies and not raw_movies_details:
                    continue

                raw_movie_data = {**raw_movies, **raw_movies_details}
                movies.append(raw_movie_data)

        return movies

    def format_movie(self, raw_movie: dict) -> dict:
        formatted_movie = {
            "title": raw_movie["title"],
            "duration": self.format_duration(raw_movie["duration"]),
            "classification": self.format_classisfication(raw_movie["classification"]),
            "cinema_name": raw_movie["cinema_name"],
            "genres": self.format_genres(raw_movie["genres"]),
            "original_title": raw_movie["original_title"],
            "country_origin": raw_movie["country_origin"],
            "director": raw_movie["director"],
            "actors": raw_movie["actors"],
            "language": raw_movie["language"],
            "synopsis": raw_movie["synopsis"],
            "image_url": raw_movie["image_url"],
        }

        return formatted_movie

    def get_raw_movies(self, movie: Tag, title: str) -> dict:
        metas = movie.find_all("span", class_="movie-item__meta")
        tags = movie.find_all("span", class_="tag")

        for meta in metas:
            text = meta.text.strip()

            if "Género" in text:
                genres = text

            elif "Duración" in text:
                duration = text

            elif "Clasificación" in text:
                classification = text

        for tag in tags:
            text = tag.text.strip()

            if "Min" in text:
                duration = text

            elif any(
                keyword in text
                for keyword in ["Min", "Para", "Exclusiva", "Recomendada"]
            ):
                classification = text

        image_url = movie.find("img")["data-src"] if movie.find("img") else ""

        movie_data = {
            "title": title,
            "cinema_name": self.cinema_name,
            "genres": genres,
            "classification": classification,
            "duration": duration,
            "image_url": image_url,
        }

        return movie_data

    def get_raw_movies_details(self, movie: Tag) -> dict | None:
        link = movie["href"]
        url = f"https://www.cinecolombia.com{link}"

        response = self.bs_driver.get_http_response(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        details = soup.find_all("div", class_="movie-details__block")
        movie_info = {}

        for detail in details:
            paragraph = detail.find("p")

            if paragraph:
                text = paragraph.get_text().strip()
                if not text:
                    text = "".join(str(c) for c in paragraph.contents)

                text = " ".join(text.split())
                position = details.index(detail)

                if position == 0:
                    movie_info["synopsis"] = text

                elif position == 1:
                    movie_info["original_title"] = text

                elif position == 2:
                    movie_info["country_origin"] = text

                elif position == 3:
                    movie_info["director"] = text

                elif position == 4:
                    movie_info["actors"] = text

                elif position == 5:
                    movie_info["language"] = text

        return movie_info

    def format_duration(self, duration: str) -> str:
        return duration + 'utos'
    def format_genres(self, genres: str) -> list[str]:
        return [genre.strip() for genre in genres.replace("Género:", "").split(",")]
    
    def format_classisfication(self, classification: str) -> str:
        return classification.capitalize()


class CineColombiaShowtimesScraper(SeleniumShowtimesScraper):
    def __init__(self, cinema_name: str, url: str) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_showtimes(self) -> list[WebElement] | None:
        links = []

        try:
            movies = self.selenium_driver.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "movie-item"))
            )

        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error al cargar elementos de películas: {e}")
            return None

        try:
            cookie_modal = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "cookie-modal"))
            )
            cookies_button = cookie_modal.find_element(By.TAG_NAME, "button")

            if cookies_button:
                cookies_button.click()

        except TimeoutException:
            print("No hay ventana de cookies")
        except NoSuchElementException:
            print("No hay botón de cookies en la ventana de cookies")

        for movie in movies:
            try:
                movie_link = movie.get_attribute("href")
                if movie_link:
                    links.append(movie_link)

            except NoSuchElementException:
                print("No se encontro el enlace de la pelúcula")
                continue

        if not links:
            print("No hay pelúculas para mostrar")
            return None

        raw_showtimes = self.get_raw_showtimes(links)

        if not raw_showtimes:
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

    def get_raw_showtimes(self, links: list[str]) -> list[dict] | None:
        showtimes = []

        for link in tqdm(
            links, desc="Scraping CineColombia showtimes", unit="showtime"
        ):
            if link is None:
                print("Link no existe")
                continue

            try:
                self.selenium_driver.get(link)

                rooms = self.selenium_driver.wait.until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "collapsible"))
                )

                raw_showtimes_details = self.get_raw_showtimes_details(rooms, link)

                if raw_showtimes_details:
                    showtimes.extend(raw_showtimes_details)

            except WebDriverException:
                print(f"No hay funciones en la página: {link}")
                continue

        return showtimes

    def get_raw_showtimes_details(
        self, rooms: list[WebElement], url: str
    ) -> list[dict]:
        showtimes = []

        try:
            movie_title = self.selenium_driver.find_element_by_class(
                "ezstring-field"
            ).text
        except NoSuchElementException:
            print(f"No se encontro el titulo en la página: {url}")
            return []

        for room in tqdm(rooms, leave=False):
            try:
                room_name = room.find_element(
                    By.CLASS_NAME, "show-times-collapse__title"
                ).text.strip()

                room.click()
            except NoSuchElementException:
                print(f"No se encontro el nombre de la sala en la página: {url}")
                continue

            try:
                schedules_elements = self.selenium_driver.wait.until(
                    EC.presence_of_all_elements_located(
                        (
                            By.CLASS_NAME,
                            "show-times-group",
                        )
                    )
                )

                showtime_data = self.scrape_schedules(
                    schedules_elements, movie_title, room_name, url
                )

                if showtime_data:
                    showtimes.extend(showtime_data)

            except (NoSuchElementException, TimeoutException) as e:
                print(f"No se encontro el horario en la página: {url}, error: {e}")
                continue

        return showtimes

    def scrape_schedules(
        self, schedules_elements: list[WebElement], title, room, url
    ) -> list[dict]:
        showtimes = []

        for schedule_element in schedules_elements:
            try:
                movie_format = schedule_element.find_element(
                    By.CLASS_NAME, "show-times-group__attrs"
                ).text

                schedules = schedule_element.find_elements(
                    By.CLASS_NAME,
                    'show-times-group__times a:not([disabled="disabled"])',
                )

                valid_schedules = [
                    schedule.text for schedule in schedules if schedule.text
                ]

                if movie_format != "" and valid_schedules:
                    for schedule in valid_schedules:
                        # Crear datos de showtime
                        showtime_data = {
                            "title": title,
                            "cinema_name": self.cinema_name,
                            "room": room,
                            "format": movie_format,
                            "date": "",
                            "schedule": schedule,
                            "url": url,
                        }

                        showtimes.append(showtime_data)

            except NoSuchElementException:
                continue

        return showtimes

    def format_date(self) -> str:
        return datetime.date.today()

    def format_schedule(self, schedule: str) -> str | None:
        schedule.replace(
            "\n",
            " ",
        ).strip()

        try:
            time_obj = datetime.datetime.strptime(schedule, "%I:%M %p").time()
            schedule_24h = time_obj.strftime("%H:%M")
        except ValueError:
            print("Error al convertir el horario de 12h a 24h")
            return None

        return schedule_24h

    def format_movie_format(self, format: str) -> str:
        return format.replace(
            "\n",
            " ",
        ).strip()
    