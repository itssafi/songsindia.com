from django.conf.urls import url
from . import views

app_name = 'music'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^songs/(?P<filter_by>[a-zA_Z]+)/$', views.SongView.as_view(), name='songs'),
    url(r'^register/$', views.UserFormView.as_view(), name='register'),
    url(r'^login/$', views.UserLoginView.as_view(), name='login'),
    # url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^album/(?P<album_id>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^album/add/$', views.AlbumCreate.as_view(), name='album-add'),
    url(r'^album/(?P<album_id>[0-9]+)/update/$', views.album_update, name='album-update'),
    url(r'^album/(?P<album_id>[0-9]+)/delete/$', views.AlbumDelete.as_view(), name='album-delete'),
    url(r'^album/(?P<album_id>[0-9]+)/favorite/$', views.album_favorite, name='album-favorite'),
    url(r'^song/add/$', views.SongCreate.as_view(), name='song-add'),
    url(r'^album/(?P<album_id>[0-9]+)/songs/(?P<song_id>[0-9]+)/delete/$', views.SongDelete.as_view(), name='song-delete'),
    url(r'^songs/favorite/(?P<filter_by>[a-zA_Z]+)/$', views.SongFavoriteView.as_view(), name='song-favorite'),
    url(r'^forget-password/$', views.ForgetPasswordView.as_view(), name='forget-password'),
    url(r'^change-password/$', views.ChangePasswordView.as_view(), name='change-password'),
]
