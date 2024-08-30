from rest_framework.routers import SimpleRouter

from oauth import views

router = SimpleRouter()
router.register('profile', views.ProfileViewSet)

urlpatterns = []
urlpatterns += router.urls
