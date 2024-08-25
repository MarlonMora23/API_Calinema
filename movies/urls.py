from rest_framework import routers
from .api import MovieViewSet, CinemaShowtimeViewSet
from .views import UpdateMoviesView, UpdateShowtimesView, UpdateAllView, CreateMoviesView, CreateShowtimesView, CreateAllView
from django.urls import path

router = routers.DefaultRouter()
router.register(r"api/movies", MovieViewSet, "movies")
router.register(r"api/cinemashowtime", CinemaShowtimeViewSet, "cinemashowtime")

urlpatterns = router.urls

# URL para ejecutar el comando update_movies que actualiza los datos de las películas
urlpatterns += [
    # Scraping
    path('api/update_movies/', UpdateMoviesView.as_view(), name='update_movies'),
    path('api/update_showtimes/', UpdateShowtimesView.as_view(), name='update_showtimes'),
    path('api/update_all/', UpdateAllView.as_view(), name='update_all'),

    # Obtener datos de la API
    path('api/create_movies/', CreateMoviesView.as_view(), name='create_movies'),
    path('api/create_showtimes/', CreateShowtimesView.as_view(), name='create_showtimes'),
    path('api/create_all/', CreateAllView.as_view(), name='create_all'),
]
