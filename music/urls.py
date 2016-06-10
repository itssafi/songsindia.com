from django.conf.urls import url
from . import views

app_name = 'music'

urlpatterns = [

    # /music/
    url(r'^$', views.IndexView.as_view(), name='index'),
    # /music/songs/
    url(r'^songs/$', views.SongView.as_view(), name='songs'),
    # /music/register/
    url(r'^register/$', views.UserFormView.as_view(), name='register'),
    # /music/login/
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    # /music/logout/
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # /music/2/
    url(r'^album/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # /music/album/add/
    url(r'album/add/$', views.AlbumCreate.as_view(), name='album-add'),
    # /music/album/2/
    url(r'album/(?P<pk>[0-9]+)/update/$', views.AlbumUpdate.as_view(), name='album-update'),
    # /music/album/2/delete/
    url(r'album/(?P<pk>[0-9]+)/delete/$', views.AlbumDelete.as_view(), name='album-delete'),
    # /music/album/2/favorite/
    url(r'album/(?P<album_id>[0-9]+)/favorite/$', views.album_favorite, name='album-favorite'),
    # /music/album/2/song/add/
    url(r'album/(?P<album_id>[0-9]+)/song/add/$', views.SongCreate.as_view(), name='song-add'),
    # /music/songs/1/delete/
    url(r'album/(?P<album_id>[0-9]+)/songs/(?P<song_id>[0-9]+)/delete/$', views.SongDelete.as_view(), name='song-delete'),
    # /music/songs/1/delete/
    url(r'song/(?P<song_id>[0-9]+)/favorite/(?P<template>[a-zA-Z]+)/$', views.song_favorite, name='song-favorite'),
]
