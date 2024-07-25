from bs4 import BeautifulSoup
from movies.scraping.scraper import (
    Scraper,
    SeleniumDriver,
    SeleniumMoviesScraper,
    SeleniumShowtimesScraper,
)
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
import datetime
import requests
from selenium.webdriver.support.ui import Select
import time


class RoyalFilmsScraper(Scraper):
    def __init__(self) -> None:
        super().__init__()
        self.cinema_name = "RoyalFilms"
        self.url = "https://royal-films.com/cartelera/cali"
        self.movies_scraper = RoyalFilmsMoviesScraper(self.cinema_name, self.url)
        self.showtimes_scraper = RoyalFilmsShowtimesScraper(self.cinema_name, self.url)


class RoyalFilmsMoviesScraper(SeleniumMoviesScraper):
    def __init__(self, cinema_name, url) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_movies(self):
        self.select_city()
        movies_data = self.selenium_driver.wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "prs_upcom_movie_box_wrapper")
            )
        )

        movies_links = self.get_movies_links(movies_data)
        raw_movies = self.get_raw_movies(movies_links)

        if not raw_movies:
            return None

        return raw_movies

    def format_movie(self, raw_movie: dict) -> dict:
        formatted_movie = {
            "title": self.format_title(raw_movie["title"]),
            "duration": self.format_duration(raw_movie["duration"]),
            "classification": self.format_classification(raw_movie["classification"]),
            "cinema_name": raw_movie["cinema_name"],
            "genres": self.format_genres(raw_movie["genres"]),
            "original_title": self.format_original_title(raw_movie["original_title"]),
            "country_origin": raw_movie["country_origin"],
            "director": self.format_director(raw_movie["director"]),
            "actors": self.format_actors(raw_movie["actors"]),
            "language": self.format_language(raw_movie["language"]),
            "synopsis": raw_movie["synopsis"],
            "image_url": raw_movie["image_url"],
        }

        return formatted_movie

    def select_city(self):
        try:
            city_card = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "card"))
            )

            list_dropdown = city_card.find_element(By.CLASS_NAME, "current")
            city_list = city_card.find_element(By.CLASS_NAME, "list")
            items = city_list.find_elements(By.TAG_NAME, "li")

            list_dropdown.click()

            for item in items:
                if item.text == "Cali":
                    item.click()
                    break
            else:
                print("No se encontró la ciudad Cali en la lista")

            submit_button = city_card.find_element(By.CLASS_NAME, "btn")
            submit_button.click()

        except WebDriverException as e:
            print(e)
            print("No se encontro la ciudad")

    def get_movies_links(self, movies_data: list[WebElement]):
        movies_links = set()

        for movie in movies_data:
            try:
                link = movie.find_element(By.TAG_NAME, "a").get_attribute("href")

                if link not in movies_links:
                    movies_links.add(link)

            except WebDriverException:
                continue

        return movies_links

    def get_raw_movies(self, movies_links: list[str]) -> list[dict]:
        raw_movies = []

        for movie_link in tqdm(
            movies_links, desc="Scraping RoyalFilms movies", unit="movie"
        ):
            try:
                raw_movie = self.get_raw_movie(movie_link)

                if not raw_movie:
                    continue

                raw_movies.append(raw_movie)

            except WebDriverException:
                continue

        return raw_movies

    def get_raw_movie(self, movie_link: str) -> dict | None:
        try:
            self.selenium_driver.get(movie_link)

            info_card = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "st_video_slide_sec"))
            )

            info_card_text = info_card.text.split("\n")

            title = info_card_text[0]
            language = info_card_text[1]
            genres = info_card_text[2]

            duration = self.selenium_driver.wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "st_video_slide_social_right.float_left")
                )
            ).text

            details_card = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "prs_syn_cont_wrapper"))
            ).text.split("\n")

            synopsis = details_card[1]
            original_title = details_card[2]
            classification = details_card[3]
            actors = details_card[4]
            director = details_card[5]

            image_container = self.selenium_driver.wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "prs_syn_img_wrapper.ng-star-inserted")
                )
            )

            image_url = image_container.find_element(By.TAG_NAME, "img").get_attribute(
                "src"
            )

            raw_movie = {
                "title": title,
                "duration": duration,
                "classification": classification,
                "cinema_name": self.cinema_name,
                "genres": genres,
                "original_title": original_title,
                "country_origin": "",
                "director": director,
                "actors": actors,
                "language": language,
                "synopsis": synopsis,
                "image_url": image_url,
            }

            return raw_movie

        except WebDriverException:
            return None

    def format_title(self, title: str) -> str:
        return title.title()

    def format_duration(self, duration: str) -> str:
        return duration.capitalize().replace("mins", "Minutos")

    def format_classification(self, classification: str) -> str:
        if "+7" in classification:
            return "Exclusiva para mayores de 7 años"

        if "+12" in classification:
            return "Exclusiva para mayores de 12 años"

        if "+15" in classification:
            return "Exclusiva para mayores de 15 años"

        if "+18" in classification:
            return "Exclusiva para mayores de 18 años"

        return "Para todo el público"

    def format_genres(self, genres: str) -> str:
        return genres.replace(" | ", ", ").title()

    def format_original_title(self, original_title: str) -> str:
        return original_title.replace("Nombre original: ", "").title()

    def format_director(self, director: str) -> str:
        return director.replace("Director: ", "").title()

    def format_actors(self, actors: str) -> str:
        return actors.replace("Reparto: ", "").title()

    def format_language(self, language: str) -> str:
        return language.capitalize()


class RoyalFilmsShowtimesScraper(SeleniumShowtimesScraper):
    def __init__(self, cinema_name, url) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_showtimes(self) -> list[dict] | None:
        self.select_city()
        movies_data = self.selenium_driver.wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "prs_upcom_movie_box_wrapper")
            )
        )

        movies_links = self.get_movies_links(movies_data)
        raw_movies = self.get_raw_showtimes(movies_links)

        if not raw_movies:
            return None

        return raw_movies

    def format_showtime(self, raw_showtime: dict) -> dict | None:
        if (
            raw_showtime["title"] != ""
            and raw_showtime["room"] != ""
            and raw_showtime["format"] != ""
            and raw_showtime["schedule"] != ""
            and raw_showtime["url"] != ""
        ):
            formatted_showtime = {
                "title": self.format_title(raw_showtime["title"]),
                "cinema_name": raw_showtime["cinema_name"],
                "room": raw_showtime["room"],
                "format": self.format_movie_format(raw_showtime["format"]),
                "date": self.format_date(),
                "schedule": self.format_schedule(raw_showtime["schedule"]),
                "url": raw_showtime["url"],
            }

            return formatted_showtime

        return None

    def select_city(self):
        try:
            city_card = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "card"))
            )

            list_dropdown = city_card.find_element(By.CLASS_NAME, "current")
            city_list = city_card.find_element(By.CLASS_NAME, "list")
            items = city_list.find_elements(By.TAG_NAME, "li")

            list_dropdown.click()

            for item in items:
                if item.text == "Cali":
                    item.click()
                    break
            else:
                print("No se encontró la ciudad Cali en la lista")

            submit_button = city_card.find_element(By.CLASS_NAME, "btn")
            submit_button.click()

        except WebDriverException as e:
            print(e)
            print("No se encontro la ciudad")

    def get_movies_links(self, movies_data: list[WebElement]):
        visited_movies_links = set()
        movies_links = []

        for movie in movies_data:
            try:
                link = movie.find_element(By.TAG_NAME, "a").get_attribute("href")

                if link not in visited_movies_links:
                    movies_links.append(link)

                visited_movies_links.add(link)

            except WebDriverException:
                continue

        return movies_links

    def get_raw_showtimes(self, movies_links: list[dict]) -> list[dict]:
        raw_movies = []

        for movie_link in tqdm(
            movies_links, desc="Scraping RoyalFilms showtimes", unit="showtime"
        ):
            if movie_link is None:
                continue

            try:
                raw_movie = self.get_raw_showtime(movie_link)

                if not raw_movie:
                    continue

                raw_movies.extend(raw_movie)

            except WebDriverException:
                continue

        return raw_movies

    def get_raw_showtime(self, movie_link: str) -> list[dict] | None:
        try:
            showtimes = []
            self.selenium_driver.get(movie_link)

            info_card = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "st_video_slide_sec"))
            )

            info_card_text = info_card.text.split("\n")

            title = info_card_text[0]

            showtimes_elements = self.selenium_driver.wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.CLASS_NAME,
                        "panel.panel-default.sidebar_pannel.ng-star-inserted",
                    )
                )
            )

            is_first = True

            for room in showtimes_elements:
                room_element = room.find_element(By.CLASS_NAME, "panel-title")
                room_name = room_element.text

                if not is_first:
                    room_element.click()

                is_first = False

                movie_formats = room.find_elements(By.CLASS_NAME, "st_calender_asc")

                for movie_format in movie_formats:
                    movie_format_text = movie_format.find_element(
                        By.TAG_NAME, "h3"
                    ).text
                    schedules = movie_format.find_elements(By.TAG_NAME, "a")

                    schedules_text = [
                        schedule.text for schedule in schedules if schedule.text != ""
                    ]

                    for schedule in schedules_text:
                        showtime = {
                            "title": title,
                            "cinema_name": self.cinema_name,
                            "room": room_name,
                            "format": movie_format_text,
                            "date": "",
                            "schedule": schedule,
                            "url": movie_link,
                        }

                        showtimes.append(showtime)

            return showtimes

        except WebDriverException:
            return None

    def format_title(self, title: str) -> str:
        return title.title()

    def format_movie_format(self, format: str) -> str:
        return format

    def format_date(self) -> str:
        return datetime.date.today()

    def format_schedule(self, schedule: str) -> str | None:
        schedule_replaced = (
            schedule.replace("a. ", "A").replace("p. ", "P").replace("m.", "M")
        )

        try:
            time_obj = datetime.datetime.strptime(schedule_replaced, "%I:%M %p").time()
            schedule_24h = time_obj.strftime("%H:%M")
        except ValueError:
            print("Error al convertir el horario de 12h a 24h")
            return None

        return schedule_24h
