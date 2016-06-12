from django.contrib.auth.models import User
from django import forms
from .models import Album, Song


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']


class AlbumForm(forms.ModelForm):

    class Meta:
        model = Album
        fields = ['artist', 'album_title', 'genre', 'album_logo', 'is_favorite']


class SongForm(forms.ModelForm):

    class Meta:
        model = Song
        fields = ['album', 'song_title', 'audio_file', 'is_favorite']

