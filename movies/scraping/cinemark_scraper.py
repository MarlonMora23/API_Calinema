from bs4 import BeautifulSoup
from movies.scraping.scraper import Scraper, SeleniumDriver, SeleniumMoviesScraper, SeleniumShowtimesScraper
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

class CineMarkScraper(Scraper):
    def __init__(self) -> None:
        super().__init__()
        self.cinema_name = "CineMark"
        self.url = 'https://www.cinemark.com.co/ciudad/cali/pacific-mall'
        self.movies_scraper = CineMarkMoviesScraper(self.cinema_name, self.url)
        self.showtimes_scraper = CineMarkShowtimesScraper(self.cinema_name, self.url)
        

class CineMarkMoviesScraper(SeleniumMoviesScraper):
    def __init__(self, cinema_name, url) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_movies(self):
        movies_data = self.selenium_driver.wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'section-detail__information-badge'))
        )

        movies_links = self.get_movies_links(movies_data)
        raw_movies = self.get_raw_movies(movies_data, movies_links)

        if not raw_movies:
            return None
        
        return raw_movies

    def format_movie(self, raw_movie):
        formatted_movie = {
            "title": self.format_title(raw_movie["title"]),
            "cinema_name": raw_movie["cinema_name"],
            "genres": raw_movie["genres"],
            "classification": self.format_classification(raw_movie["classification"]),
            "duration": self.format_duration(raw_movie["duration"]),
            "image_url": raw_movie["image_url"],
            "synopsis": raw_movie["synopsis"],
            "original_title": raw_movie["original_title"],
            "country_origin": raw_movie["country_origin"],
            "director": raw_movie["director"],
            "actors": raw_movie["actors"],
            "language": raw_movie["language"],
        }

        return formatted_movie
    
    def get_movies_links(self, movies_data: list[WebElement]):
        movies_links = []
        movies_links_set = set()
        
        for movie in movies_data:
            try:
                link = movie.find_element(By.TAG_NAME, 'a').get_attribute('href')

                if link not in movies_links_set:
                    movies_links_set.add(link)
                    movies_links.append(link)

            except WebDriverException:
                continue

        return movies_links
    
    def get_raw_movies(self, movies_data: list[WebElement], movies_links: list[str]) -> list[dict]:
        raw_movies = []
        raw_movies_details = []
        raw_movies_set = set()

        for movie in movies_data:
            try:
                raw_movie = self.get_raw_movie(movie, raw_movies_set)

                if not raw_movie:
                    continue
                
                raw_movies.append(raw_movie)

            except WebDriverException:
                continue

        for link in tqdm(movies_links, desc="Scraping CineMark movies", unit="movie"):
            raw_movie_details = self.get_raw_movie_details(link)

            if not raw_movie_details:
                continue

            raw_movies_details.append(raw_movie_details)

        for raw_movie, raw_movie_details in zip(raw_movies, raw_movies_details):
            raw_movie.update(raw_movie_details)

        return raw_movies
    
    def get_raw_movie(self, movie: WebElement, raw_movies_set: set):
        try:
            raw_movie = {}
            title = movie.find_element(By.CLASS_NAME, 'section-detail__title--bold').text.strip()
            duration = movie.find_element(By.CLASS_NAME, 'clasification--TIME').text.strip()
            classification = movie.text
            
            # Verificar si el enlace ya se ha procesado
            if movie not in raw_movies_set and title != '':
                raw_movies_set.add(movie)

            raw_movie = {
                'title': title,
                'cinema_name' : self.cinema_name,
                'genres': '',
                'classification': classification,
                'duration': duration,
            }

            return raw_movie
        
        except WebDriverException:
            return None

    def get_raw_movie_details(self, link: str):
        try:
            raw_movie_details = {}
            self.selenium_driver.get(link)
            details_container = self.selenium_driver.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'detailMovie__container'))
            )
            titulo_original = details_container.find_element(By.XPATH, "//h4[text()='título original']/following-sibling::p").text
            actores = details_container.find_element(By.XPATH, "//h4[text()='reparto']/following-sibling::p").text
            img = details_container.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div[1]/div[3]/div/div[1]/div/img').get_attribute('src')

            try:
                sinopsis_boton = details_container.find_element(By.XPATH,'//*[@id="__next"]/div[2]/div[2]/div[1]/div[3]/div/p[3]/span[2]')
                if sinopsis_boton:
                    sinopsis_boton.click()

                sinopsis = details_container.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div[1]/div[3]/div/p[3]/span[1]').text.strip()
            
            except NoSuchElementException:
                sinopsis = details_container.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[2]/div[1]/div[3]/div/p[3]/span[1]').text.strip()

            raw_movie_details = {
                'image_url': img,
                'synopsis': sinopsis,
                'original_title': titulo_original,
                'country_origin': '',
                'director': '',
                'actors': actores,
                'language': '',
            }

            return raw_movie_details
        
        except WebDriverException:
            return None
        
    def format_title(self, title: str) -> str:
        return title.title()
    
    def format_classification(self, classification):
        if "+ 7" in classification:
            return "Exclusiva para mayores de 7 años"
        
        if "+ 12" in classification:
            return "Exclusiva para mayores de 12 años"
        
        if "+ 15" in classification:
            return "Exclusiva para mayores de 15 años"
        
        if "+ 18" in classification:
            return "Exclusiva para mayores de 18 años"
        
        return "Para todo el público"
    
    def format_duration(self, duration: str) -> str:
        return duration.title()


class CineMarkShowtimesScraper(SeleniumShowtimesScraper):
    def __init__(self, cinema_name, url) -> None:
        super().__init__()
        self.cinema_name = cinema_name
        self.url = url

    def scrape_showtimes(self):
        raw_showtimes = []

        movies_data = self.selenium_driver.wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'section-detail__schedule'))
        )
            
        for movie in tqdm(movies_data, desc="Scraping CineMark showtimes", unit="showtime"):
            try:
                showtime = self.get_schedules(movie)

                if not showtime:
                    continue

                raw_showtimes.extend(showtime)

            except WebDriverException: 
                continue

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
                "title": self.format_title(raw_showtime["title"]),
                "cinema_name": raw_showtime["cinema_name"],
                "room": raw_showtime["room"],
                "format": self.format_movie_format(raw_showtime["format"]),
                "date": self.format_date(),
                "schedule": raw_showtime["schedule"],
                "url": raw_showtime["url"],
            }

            return formatted_showtime

        return None
    
    def get_schedules(self, movie: WebElement):
        showtimes = []
        title = movie.find_element(By.CLASS_NAME, 'section-detail__title').text.strip()
        container = movie.find_elements(By.CLASS_NAME, 'theater-detail__container--principal__co')
        url = movie.find_element(By.TAG_NAME, 'a').get_attribute('href') 

        for contain in container:
            try:
                formats_element = contain.find_elements(By.CSS_SELECTOR, ".formats__item")
                schedules_element = contain.find_elements(By.CLASS_NAME, "sessions__button--runtime")

                formats = [format_element.text for format_element in formats_element]
                movie_format = ' '.join(formats)
                schedules = [schedule_element.text for schedule_element in schedules_element]

                for schedule in schedules:
                    showtime = {
                        'title': title,
                        'cinema_name': self.cinema_name,
                        'room': 'Pacific Mall',
                        'format': movie_format,
                        'date': '',
                        'schedule': schedule,
                        'url': url
                    }

                    showtimes.append(showtime)

            except WebDriverException: 
                continue

        return showtimes

    def format_title(self, title: str) -> str:
        return title.title()
    
    def format_movie_format(self, format: str) -> str:
        return format.title()
    
    def format_date(self) -> str:
        return datetime.date.today()
