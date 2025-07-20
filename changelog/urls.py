from django.urls import path

from changelog.views import ActivityView

urlpatterns = [
    path('activity/', ActivityView.as_view()),
]
