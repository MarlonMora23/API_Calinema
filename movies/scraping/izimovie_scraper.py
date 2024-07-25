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
import time


class IziMovieScraper(Scraper):
    def __init__(self) -> None:
        super().__init__()
        self.cinema_name = "IziMovie"
        self.url = "https://izi.movie/"
        self.movies_scraper = IziMovieMovieScraper(self.cinema_name, self.url)
        self.showtimes_scraper = IziMovieShowtimesScraper(self.cinema_name, self.url)


class IziMovieMovieScraper(SeleniumMoviesScraper):
    def __init__(self, cinema_name: str, url) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url + "programacion.php"

    def scrape_movies(self):
        try:
            movies_data = self.selenium_driver.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "movie"))
            )

            raw_movies = self.get_raw_movies(movies_data)

            if not raw_movies:
                return None

            return raw_movies

        except WebDriverException:
            return None

    def format_movie(self, raw_movie: dict) -> dict:
        return {
            "title": self.format_title(raw_movie["title"]),
            "duration": self.format_duration(raw_movie["duration"]),
            "classification": self.format_classification(raw_movie["classification"]),
            "cinema_name": raw_movie["cinema_name"],
            "genres": self.format_genres(raw_movie["genres"]),
            "original_title": raw_movie["original_title"],
            "country_origin": raw_movie["country_origin"],
            "director": raw_movie["director"],
            "actors": raw_movie["actors"],
            "language": raw_movie["language"],
            "synopsis": self.format_synopsis(raw_movie["synopsis"]),
            "image_url": raw_movie["image_url"],
        }

    def get_raw_movies(self, movies_data: list[WebElement]) -> list[dict]:
        raw_movies = []

        for movie in tqdm(movies_data, desc="Scraping IziMovie Movies", unit="movie"):
            try:
                title = movie.find_element(
                    By.CLASS_NAME, "movie__title"
                ).text.strip()
                duration = movie.find_element(By.CLASS_NAME, "movie__time").text.strip()
                details_container = movie.find_elements(By.CLASS_NAME, "movie__option")

                genres = details_container[0].text
                classification = details_container[1].text
                synopsis = details_container[4].text

                image_url = (
                    movie.find_element(By.CLASS_NAME, "movie__images")
                    .find_element(By.TAG_NAME, "img")
                    .get_attribute("src")
                )

                raw_movie = {
                    "title": title,
                    "duration": duration,
                    "classification": classification,
                    "cinema_name": self.cinema_name,
                    "genres": genres,
                    "original_title": "",
                    "country_origin": "",
                    "director": "",
                    "actors": "",
                    "language": "",
                    "synopsis": synopsis,
                    "image_url": image_url,
                }

                raw_movies.append(raw_movie)

            except NoSuchElementException:
                continue

        return raw_movies

    def format_title(self, title: str) -> str:
        return title.title()
    
    def format_duration(self, duration: str) -> str:
        return duration.title() + "utos"
    
    def format_classification(self, classification: str) -> str:
        formatted_classification = classification.split("Clasificación: ")[-1]

        if formatted_classification == "Todo Publico" :
            formatted_classification = "Para todo el público"

        elif formatted_classification == "7":
            formatted_classification = "Exclusivo para mayores de 7 años"

        elif formatted_classification == "12":
            formatted_classification = "Exclusiva para mayores de 12 años"

        elif formatted_classification == "15":
            formatted_classification = "Exclusiva para mayores de 15 años"

        elif formatted_classification == "18":
            formatted_classification = "Exclusiva para mayores de 18 años"

        return formatted_classification
    
    def format_synopsis(self, synopsis: str) -> str:
        return synopsis.split("Sinopsis: ")[-1]
    
    def format_genres(self, genres: str) -> str:
        return genres.split("Género: ")[-1]
    
    def format_synopsis(self, synopsis: str) -> str:
        return synopsis.split("Sinopsis: ")[-1]
    


class IziMovieShowtimesScraper(SeleniumShowtimesScraper):
    def __init__(self, cinema_name: str, url: str) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_showtimes(self):
        raw_showtimes = []
        try:
            movies = self.selenium_driver.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "movie--time"))
            )

            raw_showtimes = self.get_raw_showtimes(movies)

            if not raw_showtimes:
                return None

            return raw_showtimes
        
        except WebDriverException:
            return None

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
    
    def get_raw_showtimes(self, movies: list[WebElement]) -> list[dict]:
        raw_showtimes = []
        for movie in tqdm(movies, desc="Scraping IziMovie Showtimes", unit="showtime"):
            try:
                title = movie.find_element(By.CLASS_NAME, "movie__title").text.strip()
                movie_details = movie.find_elements(By.CLASS_NAME, "movie__option")

                movie_format = movie_details[0].text
                schedules = movie.find_elements(
                    By.CLASS_NAME, "time-select__item"
                )
                url = movie.find_element(By.CLASS_NAME, "movie__title").get_attribute(
                    "href"
                )

                for schedule in schedules:
                    raw_showtime = {
                        "title": title,
                        "cinema_name": self.cinema_name,
                        "room": "Aquarela",
                        "format": movie_format,
                        "date": "",
                        "schedule": schedule.text,
                        "url": url,
                    }

                    raw_showtimes.append(raw_showtime)

            except NoSuchElementException:
                continue

        return raw_showtimes
    
    def format_title(self, title: str) -> str:
        return title.title()
    
    def format_movie_format(self, movie_format: str) -> str:
        return movie_format.split("Tipo: ")[-1]
    
    def format_date(self):
        return datetime.date.today()
    
    def format_schedule(self, schedule: str) -> str:
        return schedule.strip().replace('*', '')
