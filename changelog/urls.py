from django.urls import path

from changelog.apis.activity import ActivityView

urlpatterns = [
    path('activity/', ActivityView.as_view()),
]
