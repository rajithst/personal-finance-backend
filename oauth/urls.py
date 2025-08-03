from django.urls import path
from rest_framework.routers import SimpleRouter

from oauth import views
from oauth.views import PasswordResetWithoutEmailView

router = SimpleRouter()
router.register('profile', views.ProfileViewSet)
urlpatterns = [
    path('users/reset_password', PasswordResetWithoutEmailView.as_view()),

]
urlpatterns += router.urls
