import re
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import Album, Song


class UserForm(UserCreationForm):
    username = forms.RegexField(label=_("Username"), regex=r'^.*(?=.{6,})(?=.*[a-z]).*$',
                                help_text=_('Required, 6 to 30 characters in lowercase.'),
                                widget=forms.TextInput(attrs=dict(required=True, max_length=15)),
                                error_messages={'invalid': _(
                                    "Username must contain only letters, 6 to 30 characters in lowercase.") })
    first_name = forms.CharField(label=_('First name'),
                                 widget=forms.TextInput(attrs=dict(required=True, max_length=30)))
    last_name = forms.CharField(label=_('Last name'),
                                widget=forms.TextInput(attrs=dict(required=True, max_length=30)))
    email = forms.EmailField(label=_("Email address"),
                             widget=forms.TextInput(attrs=dict(required=True, max_length=50)))
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs=dict(required=True,
                                                                      max_length=30,
                                                                      render_value=False)))

    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_("The username already exists. Please try another one."))
 
    def clean_password2(self):
        pattern = '^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=]).*$'
        if not re.findall(pattern, self.cleaned_data['password1']):
            err_text = """Your password must follow all of these:\n\t
            1. At least 8 characters.\n\t
            2. Uppercase letter.\n\t
            3. Lowercase letter.\n\t
            4. Numeric.\n\t
            5. Any of the special characters: ! @ # $ % ^ * + = """
            raise forms.ValidationError(_(err_text))

        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data['password1']

    def clean_email(self):
        try:
            user = User.objects.get(email__iexact=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']
        raise forms.ValidationError(_("The email address already exists. Please try another one."))

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
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

    class Meta:
        model = Album
        fields = ['artist', 'album_title', 'genre', 'album_logo', 'is_favorite']


class SongForm(forms.ModelForm):
    song_title = forms.CharField(label=_('Song title'),
                                 widget=forms.TextInput(attrs=dict(required=True, max_length=250)))

    class Meta:
        model = Song
        fields = ['album', 'song_title', 'audio_file', 'is_favorite']

