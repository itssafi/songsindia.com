import random, string
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.utils.http import is_safe_url
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View, FormView, RedirectView
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import Album, Song
from .forms import UserForm, AlbumForm, SongForm
from utils.forms.reset_password_form import PasswordResetForm, ChangePasswordForm


class IndexView(generic.ListView):
    template_name = 'music/index.html'
    context_object_name = 'albums'

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            self.template_name = 'music/login.html'
            return
        albums = Album.objects.filter(user=self.request.user)
        song_results = Song.objects.all()
        query = self.request.GET.get('search')
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            if song_results:
                self.context_object_name = 'song_results'
                return song_results
        return albums


class SongView(View):

    def get(self, request, filter_by):
        if not self.request.user.is_authenticated():
            return render(request, 'music/login.html')
        try:
            song_ids = []
            for album in Album.objects.filter(user=self.request.user):
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids)
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'all_songs': users_songs,
            'filter_by': filter_by,
        })


class DetailView(generic.DetailView):
    model = Album
    template_name = 'music/detail.html'


class AlbumCreate(View):
    form_class = AlbumForm
    template_name = 'music/album_form.html'

    # Display blank form
    def get(self, request):
        if not request.user.is_authenticated():
            return render(request, 'music/login.html')
        
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated():
            return render(request, 'music/login.html')

        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.album_logo = request.FILES['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, self.template_name, context)
            album.save()
            albums = Album.objects.filter(user=request.user)
            return render(request, 'music/index.html', {'albums': albums})
        context = {
            "form": form,
        }
        return render(request, self.template_name, context)


def album_update(request, album_id):
    template_name = 'music/album_update_form.html'

    if not request.user.is_authenticated():
        return render(request, 'music/login.html')

    album = Album.objects.get(id=album_id)
    if request.POST:
        form = AlbumForm(request.POST or None, request.FILES or None, instance=album)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            if hasattr(request.POST, 'album_logo'):
                album.album_logo = request.POST['album_logo']
            file_type = album.album_logo.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in settings.IMAGE_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Image file must be PNG, JPG, or JPEG',
                }
                return render(request, template_name, context)
            album.save()
            albums = Album.objects.filter(user=request.user)
            return render(request, 'music/index.html', {'albums': albums})
        context = {
            "form": form,
        }
        return render(request, template_name, context)
    else:
        form = AlbumForm(instance=album)
        return render(request, template_name, {'form': form})


class AlbumDelete(DeleteView):
    model = Album
    success_url = reverse_lazy('music:index')


class SongCreate(View):
    form_class = SongForm
    template_name = 'music/song_form.html'

    # Display blank form
    def get(self, request, album_id):
        if not request.user.is_authenticated():
            return render(request, 'music/login.html')

        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request, album_id):
        if not request.user.is_authenticated():
            return render(request, 'music/login.html')
        
        album = get_object_or_404(Album, pk=album_id)
        form = SongForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            albums_songs = album.song_set.all()
            for song in albums_songs:
                if song.song_title == form.cleaned_data.get("song_title"):
                    context = {
                        'album': album,
                        'form': form,
                        'error_message': 'You already added that song',
                    }
                    return render(request, self.template_name, context)
            song = form.save(commit=False)
            song.album = album
            song.audio_file = request.FILES['audio_file']
            file_type = song.audio_file.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in settings.AUDIO_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Audio file must be WAV, MP3, MP4 or OGG',
                }
                return render(request, self.template_name, context)
            song.save()
            return render(request, 'music/detail.html', {'album': album})
        context = {
            'album': album,
            'form': form,
        }
        return render(request, 'music/song_form.html', context)


class SongDelete(View):

    def post(self, request, album_id, song_id):
        album = get_object_or_404(Album, pk=album_id)
        song = Song.objects.get(pk=song_id)
        song.delete()
        return render(request, 'music/detail.html', {'album': album})


def song_favorite(request, song_id, template):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')
    song_ids = []
    albums = Album.objects.filter(user=request.user)
    for album in albums:
        for song in album.song_set.all():
            song_ids.append(song.pk)
    songs = Song.objects.filter(pk__in=song_ids)
    song = get_object_or_404(Song, pk=song_id)
    try:
        if song.is_favorite:
            song.is_favorite = False
        else:
            song.is_favorite = True
        song.save()
    except (KeyError, Song.DoesNotExist):
        if template == 'songs':
            return render(request, 'music/songs.html',
                          {'all_songs': songs, 'error_message': 'Song does not exists'})
        else:
            return render(request, 'music/index.html',
                          {'albums': albums, 'error_message': 'Song does not exists'})
    else:
        for album in albums:
            for song in album.song_set.all():
                song_ids.append(song.pk)
        songs = Song.objects.filter(pk__in=song_ids)
        if template == 'songs':
            return render(request, 'music/songs.html', {'all_songs': songs})
        else:
            album = get_object_or_404(Album, pk=song.album_id)
            return render(request, 'music/detail.html', {'album': album})


def album_favorite(request, album_id):
    if not request.user.is_authenticated():
        return render(request, 'music/login.html')

    albums = Album.objects.filter(user=request.user)
    album = get_object_or_404(Album, pk=album_id)
    try:
        if album.is_favorite:
            album.is_favorite = False
        else:
            album.is_favorite = True
        album.save()
    except (KeyError, Album.DoesNotExist):
        context = {
            'albums': albums,
            'error_message': 'Album does not exists.',
        }
        return render(request, 'music/index.html', context)
    else:
        albums = Album.objects.filter(user=request.user)
        return render(request, 'music/index.html', {'albums': albums})


class UserFormView(View):
    form_class = UserForm
    template_name = 'music/registration_form.html'

    # Display blank form
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Cleaned normalized data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            # Returns User objects if credentials are correct
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # send_mail('Welcome to SongsIndia.com', 'Mail body', settings.EMAIL_HOST_NAME,
                    #           [form.email], fail_silently=True)
                    return redirect('music:index')
        return render(request, self.template_name, {'form': form})


def user_login(request):
    login_template = 'music/login.html'
    if request.method == "POST":
        username = request.POST['username']
        if not User.objects.filter(username=username):
            return render(request, login_template, {'error_message': 'Username does not exists.'})
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                albums = Album.objects.filter(user=request.user)
                return render(request, 'music/index.html', {'albums': albums})
            else:
                return render(request, login_template, {'error_message': 'Your account has been disabled'})
        else:
            return render(request, login_template, {'error_message': 'Username or password is incorrect.'})
    return render(request, login_template)


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/music/login/'

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)


class ForgetPasswordView(View):
    form_class = PasswordResetForm
    template_name = 'music/forget_password.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            username = form.cleaned_data['username']
            email = form.cleaned_data['email_address']
            try:
                user = User.objects.get(Q(username=username) & Q(email=email))

            except User.DoesNotExist:
                context = {'form': form,
                           'error_message': 'Username and email address does not associated each other.'}
                return render(request, self.template_name, context)
            user.is_active = True
            if not user.is_active:
                context = {'form': form,
                           'error_message': 'Your account has been disabled'}
                return render(request, self.template_name, context)

            temp_pass = ''.join(random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
            user.set_password(temp_pass)
            user.is_active = False

            email_body = """Hello {0},\n\nYour SongsIndia credentials:\n\n\t
            Username: {1}\n\tTemporary Password: {2}\n\nPlease <a href="{3}">click here</a>
            to reset your password\n\n\n\nRegards,\nSongsIndia Team""".format(
                user.first_name, user.username, temp_pass, self.request.get_raw_uri())
            
            subject = 'Reset Password - SongsIndia.com'
            # send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL,
            #           [email], fail_silently=True)
            context = {'form': form,
                       'success_message':
                       'An email has been sent to {0}. Please check its inbox to continue reseting password({1}).'.format(email, temp_pass)}
            user.save()
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})


class ChangePasswordView(View):
    form_class = ChangePasswordForm
    template_name = 'music/change_password.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Cleaned normalized data
            username = form.cleaned_data['username']
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            try:
                user = User.objects.get(username=username)

            except User.DoesNotExist:
                context = {'form': form,
                           'error_message': 'Username does not exists.'}
                return render(request, self.template_name, context)
            user = authenticate(username=username, password=current_password)
            if not user:
                context = {'form': form,
                           'error_message': 'Current password is incorrect.'}
                return render(request, self.template_name, context)
            # import pdb; pdb.set_trace()
            if new_password != confirm_password:
                context = {'form': form,
                           'error_message': 'Password mis-match.'}
                return render(request, self.template_name, context)
            user.set_password(new_password)
            user.is_active = True
            context = {'success_message':
                       'Password has been changed successfully. Please login with the changed password.'}
            user.save()
            return render(request, self.template_name, context)
        return render(request, self.template_name, {'form': form})
