from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
import datetime
import requests

class Scraper:
    def __init__(self):
        self.cinema_name = None
        self.url = None
        self.movies_scraper = None
        self.showtimes_scraper = None

    def get_movies(self):
        self.movies_scraper.update_movies()
        return self.movies_scraper.get_movies()

    def get_showtimes(self):
        self.showtimes_scraper.update_showtimes()
        return self.showtimes_scraper.get_showtimes()
    
    def get_cinema_name(self):
        return self.cinema_name
    

class BeautifulSoupDriver:
    def __init__(self):
        self.driver = requests

    def get_http_response(self, url) -> requests.Response | None:
        response = self.driver.get(url)

        if response.status_code != 200:
            raise requests.HTTPError(
                f"Error al obtener la lista de películas. Código de estado: {response.status_code}"
            )
        
        return response
            
    
class BeautifulSoupMoviesScraper:
    def __init__(self):
        self.bs_driver = BeautifulSoupDriver()
        self.movies = None

    def set_movies(self, movies):
        self.movies = movies

    def get_movies(self):
        return self.movies

    def update_movies(self) -> list[dict] | None:
        response = self.bs_driver.get_http_response(self.url)
        
        if not response:
            return None

        movies = self.get_today_movies(response)
        self.set_movies(movies)

    def get_today_movies(self, response: requests.Response) -> list[dict] | None:
        soup = BeautifulSoup(response.text, "html.parser")
        raw_movies = self.scrape_movies(soup)
        formatted_movies = [self.format_movie(raw_movie) for raw_movie in raw_movies]

        # Guardar solo los datos que no sean None
        valid_formatted_movies = [movie for movie in formatted_movies if movie]

        if not valid_formatted_movies:
            print("No se encontraron películas en la página")
            return None

        return valid_formatted_movies
    

class SeleniumDriver:
    def __init__(self) -> None:
        self.driver = self.get_driver()
        self.wait_time = 3
        self.wait = WebDriverWait(self.driver, self.wait_time)

    def get(self, url):
        self.driver.get(url)

    def find_element_by_class(self, class_name):
        return self.driver.find_element(By.CLASS_NAME, class_name)
    
    def find_element_by_path(self, path):
        return self.driver.find_element(By.XPATH, path)

    @staticmethod
    def get_driver():
        options = webdriver.EdgeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")
        options.add_argument("--silent")

        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)

        return driver

    def quit(self):
        self.driver.quit()
    
class SeleniumMoviesScraper:
    def __init__(self) -> None:
        self.selenium_driver = None
        self.cinema_name = None
        self.url = None
        self.movies = None

    def set_movies(self, movies):
        self.movies = movies

    def get_movies(self):
        return self.movies
    
    def update_movies(self):
        try:
            self.selenium_driver = SeleniumDriver()
            self.selenium_driver.get(self.url)
            movies = self.get_today_movies()
            self.set_movies(movies)

        except WebDriverException as e:
            print(f"Error al cargar la página de {self.cinema_name}: {e}")
            return None

        finally:
            self.selenium_driver.quit()

    def get_today_movies(self):
        raw_movies = self.scrape_movies()

        if not raw_movies:
            print(f"No se encontraron películas en la página de {self.cinema_name}")
            return None
        
        formatted_movies = [self.format_movie(movie) for movie in raw_movies]

        # Guardar solo los datos que no sean None
        valid_formatted_movies = [movie for movie in formatted_movies if movie]

        if not valid_formatted_movies:
            print(f"No se encontraron películas en la página de {self.cinema_name}")
            return None

        return valid_formatted_movies
    

class SeleniumShowtimesScraper:
    def __init__(self) -> None:
        self.selenium_driver = None
        self.cinema_name = None
        self.url = None
        self.showtimes = None
        

    def set_showtimes(self, showtimes):
        self.showtimes = showtimes

    def get_showtimes(self):
        return self.showtimes

    def update_showtimes(self) -> list[dict] | None:
        try:
            self.selenium_driver = SeleniumDriver()
            self.selenium_driver.get(self.url)
            showtimes = self.get_today_showtimes()
            self.set_showtimes(showtimes)

        except WebDriverException as e:
            print(f"Error al cargar la página de {self.cinema_name}: {e}")
            return None

        finally:
            self.selenium_driver.quit()

    def get_today_showtimes(self) -> list[dict] | None:
        raw_showtimes = self.scrape_showtimes()

        if not raw_showtimes:
            print(f"No se encontraron funciones en la página de {self.cinema_name}")
            return None
        
        formatted_showtimes = [
            self.format_showtime(raw_shotime) for raw_shotime in raw_showtimes
        ]

        # Guardar solo los datos que no sean None
        valid_formatted_showtimes = [
            showtime for showtime in formatted_showtimes if showtime
        ]

        if not valid_formatted_showtimes:
            print(f"No se encontraron funciones en la página de {self.cinema_name}")
            return None

        return valid_formatted_showtimes
  