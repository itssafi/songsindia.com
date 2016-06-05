from django.conf.urls import url
from . import views

app_name = 'music'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),

    url(r'^register/$', views.UserFormView.as_view(), name='register'),

    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),

    # /music/album/add/
    url(r'album/add/$', views.AlbumCreate.as_view(), name='album-add'),

    # /music/album/2/
    url(r'album/(?P<pk>[0-9]+)/$', views.AlbumUpdate.as_view(), name='album-update'),

    # /music/album/2/delete/
    url(r'album/(?P<pk>[0-9]+)/delete/$', views.AlbumDelete.as_view(), name='album-delete'),

    # /music/album/2/favorite/
    url(r'album/(?P<pk>[0-9]+)/favorite/$', views.AlbumFavorite.as_view(), name='album-favorite'),

    # /music/album/2/song/1/delete/
    url(r'song/(?P<pk>[0-9]+)/delete/$', views.SongDelete.as_view(), name='song-delete'),

    # /music/album/2/song/add/
    url(r'album/(?P<pk>[0-9]+)/song/add/$', views.SongCreate.as_view(), name='song-add'),
]
