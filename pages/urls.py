
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("grant-acceptance/", views.grant_acceptance, name="grant_acceptance"),
    path("suggestions/", views.suggestions, name="suggestions"),
    path("submit-grant/", views.submit_grant, name="submit_grant"),
    path("submit-suggestion/", views.submit_suggestion, name="submit_suggestion"),
]