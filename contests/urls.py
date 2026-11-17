from django.urls import path

from . import views

app_name = "contests"

urlpatterns = [
    path("", views.contest_list, name="contest_list"),
    path("contests/new/", views.contest_create, name="contest_create"),
    path("contests/<str:date>/", views.contest_detail, name="contest_detail"),
    path("contests/<str:date>/edit/", views.contest_edit, name="contest_edit"),
    path("contests/<str:date>/delete/", views.contest_delete, name="contest_delete"),
    path("contests/<str:date>/entries/new/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
    path("songs/", views.song_list, name="song_list"),
    path("songs/new/", views.song_create, name="song_create"),
    path("songs/<int:pk>/edit/", views.song_edit, name="song_edit"),
    path("songs/<int:pk>/delete/", views.song_delete, name="song_delete"),
    path("ranking/", views.ranking, name="ranking"),
]
