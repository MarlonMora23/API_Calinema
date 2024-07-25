from rest_framework import routers
from .api import MovieViewSet, CinemaShowtimeViewSet
from .views import UpdateMoviesView, UpdateShowtimesView, UpdateAllView
from django.urls import path

router = routers.DefaultRouter()
router.register(r"api/movies", MovieViewSet, "movies")
router.register(r"api/cinemashowtime", CinemaShowtimeViewSet, "cinemashowtime")

urlpatterns = router.urls

# URL para ejecutar el comando update_movies que actualiza los datos de las películas
urlpatterns += [
    path('api/update_movies/', UpdateMoviesView.as_view(), name='update_movies'),
    path('api/update_showtimes/', UpdateShowtimesView.as_view(), name='update_showtimes'),
    path('api/update_all/', UpdateAllView.as_view(), name='update_all'),
]
