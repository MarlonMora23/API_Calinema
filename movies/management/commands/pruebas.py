from typing import Any
from movies.scraping.cinecolombia_scraper import CineColombiaScraper
from movies.scraping.cinepolis_scraper import CinepolisScraper
from movies.scraping.cinemark_scraper import CineMarkScraper
from movies.scraping.izimovie_scraper import IziMovieScraper
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        izimovie_scraper = IziMovieScraper()
        izimovie_showtimes = izimovie_scraper.get_showtimes()

        print(izimovie_showtimes)