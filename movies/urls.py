from rest_framework import routers
from .api import MovieViewSet, CinemaShowtimeViewSet

router = routers.DefaultRouter()
router.register(r"api/movies", MovieViewSet, "movies")
router.register(r"api/cinemashowtime", CinemaShowtimeViewSet, "cinemashowtime")

urlpatterns = router.urls
