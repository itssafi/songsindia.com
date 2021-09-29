from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from music.models import Album, Song


class AlbumForm(forms.ModelForm):
    artist = forms.CharField(label=_('Artist name'),
                             widget=forms.TextInput(attrs=dict(required=True, max_length=250)))
    album_title = forms.CharField(label=_('Album title'),
                                  widget=forms.TextInput(attrs=dict(required=True, max_length=500)))
    genre = forms.CharField(label=_('Genre'),
                            widget=forms.TextInput(attrs=dict(required=True, max_length=100)))
    album_logo = forms.FileField(label=_('Album logo'))

    class Meta:
        model = Album
        fields = ['artist', 'album_title', 'genre', 'album_logo', 'is_favorite']

    def clean_album_logo(self):
        if self.cleaned_data['album_logo']:
            if hasattr(self.cleaned_data['album_logo'], 'content_type') or 'album_logo' in self.changed_data:
                album_logo = self.cleaned_data['album_logo']
                file_type = str(album_logo._name).split('.')[-1]
                if file_type.upper() not in settings.IMAGE_FILE_TYPES:
                    raise forms.ValidationError(_(
                        "Image file must be %s." % ', '.join(settings.IMAGE_FILE_TYPES)))

                file_size = album_logo.size / float(1024**2)
                if file_size > 1.5:
                    raise forms.ValidationError(_('Maximum album logo file size is 1.5MB.'))
                return self.cleaned_data['album_logo']


class AlbumFormUpdate(AlbumForm):
    album_logo = forms.FileField(label=_('Album logo'), required=False)    


class SongForm(forms.ModelForm):
    song_title = forms.CharField(label=_('Song title'),
                                 widget=forms.TextInput(attrs=dict(required=True, max_length=250)))
    audio_file = forms.FileField(label=_('Audio file'))

    class Meta:
        model = Song
        fields = ['album', 'song_title', 'audio_file', 'is_favorite']

    def clean_audio_file(self):
        audio_file = self.cleaned_data['audio_file']
        file_type = str(audio_file._name).split('.')[-1]
        if file_type.upper() not in settings.AUDIO_FILE_TYPES:
            raise forms.ValidationError(_(
                "Audio file must be %s." % ', '.join(settings.AUDIO_FILE_TYPES)))

        file_size = audio_file.size / float(1024**2)
        if file_size > 7.0:
            raise forms.ValidationError(_('Maximum audio file size is 7MB.'))
        return self.cleaned_data['audio_file']
