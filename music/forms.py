import re
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from .models import Album, Song, User


class UserForm(UserCreationForm):
    username = forms.RegexField(label=_("Username"), regex=r'^.*(?=.{6,})(?=.*[a-z]).*$',
                                help_text=_('Required, 6 to 30 characters in lowercase.'),
                                widget=forms.TextInput(attrs=dict(required=True,
                                    max_length=15, placeholder='Username')),
                                error_messages={'invalid': _(
                                    "Username must contain only letters, 6 to 30 characters in lowercase.")})
    first_name = forms.CharField(label=_('First name'),
                                 widget=forms.TextInput(attrs=dict(required=True,
                                    max_length=30, placeholder='First name')))
    last_name = forms.CharField(label=_('Last name'),
                                widget=forms.TextInput(attrs=dict(required=True,
                                    max_length=30, placeholder='Last name')))
    email = forms.EmailField(label=_("Email address"),
                             widget=forms.TextInput(attrs=dict(required=True,
                                max_length=50,  placeholder='Enter your Email ID')))
    pattern = r'^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=]).*$'
    err_text = """Your password must have all of these:\n\t
            1. At least 8 characters.\n\t
            2. Uppercase letter.\n\t
            3. Lowercase letter.\n\t
            4. Numeric.\n\t
            5. Any of the special characters: ! @ # $ % ^ * + = """
    phone_number = forms.RegexField(label=_("Phone number"),
                                    regex=r'^([+][0-9]{1,3})([0-9]{10,11})$',
                                    widget=forms.TextInput(attrs=dict(required=True,
                                        max_length=15, placeholder='+910123456789')),
                                    error_messages={'invalid': _(
                                        "Phone number must be entered with country code. Up to 15 digits allowed.")})
    password1 = forms.RegexField(label=_("Password"), regex=pattern,
                                 error_messages={'invalid': _(err_text)},
                                 widget=forms.PasswordInput(attrs=dict(required=True,
                                                                       max_length=30,
                                                                       render_value=False,
                                                                        placeholder='Password')))
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False,
                                                                       placeholder='Password Confirmation')))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'password1']

    def clean_username(self):
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_("The username already exists. Please try another one."))
 
    def clean_password2(self):
        if self.cleaned_data.has_key('password1'):
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
            return self.cleaned_data['password1']

    def clean_email(self):
        try:
            user = User.objects.get(email__iexact=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError(_("The email address already used. Please try another one."))

    def clean_phone_number(self):
        try:
            user = User.objects.get(phone_number__iexact=self.cleaned_data['phone_number'])
        except User.DoesNotExist:
            return self.cleaned_data['phone_number']
        raise forms.ValidationError(_("The phone number already used. Please try another one."))

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


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
