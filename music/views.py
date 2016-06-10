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
from django.db.models import Q
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .models import Album, Song
from .forms import UserForm, AlbumForm, SongForm

AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']


class IndexView(generic.ListView):
    template_name = 'music/index.html'
    context_object_name = 'albums'

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            self.template_name = 'music/login.html'
            return
        else:
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


class SongView(generic.ListView):
    template_name = 'music/songs.html'
    context_object_name = 'all_songs'

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            self.template_name = 'music/login.html'
            return
        else:
            try:
                song_ids = []
                filter_by = 'all'
                for album in Album.objects.filter(user=self.request.user):
                    for song in album.song_set.all():
                        song_ids.append(song.pk)
                users_songs = Song.objects.filter(pk__in=song_ids)
                if filter_by == 'favorites':
                    users_songs = users_songs.filter(is_favorite=True)
            except Album.DoesNotExist:
                users_songs = []
        return users_songs


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
        else:
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated():
            return render(request, 'music/login.html')
        else:
            form = AlbumForm(request.POST or None, request.FILES or None)
            # form = self.form_class(request.POST)
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
                    return render(request, 'music/album_form.html', context)
                album.save()
                albums = Album.objects.filter(user=request.user)
                return render(request, 'music/index.html', {'albums': albums})
            context = {
                "form": form,
            }
            return render(request, 'music/album_form.html', context)


class AlbumUpdate(UpdateView):
    # form_class = AlbumForm
    # template_name = 'music/album_update_form.html'
    #
    # # Display form with existing data
    # def get(self, request, album_id):
    #     if not request.user.is_authenticated():
    #         return render(request, 'music/login.html')
    #     else:
    #         album = Album.objects.filter(id=album_id)
    #         # import pdb; pdb.set_trace()
    #         form = self.form_class(None)
    #         return render(request, self.template_name, {'form': form})
    #
    # # Process form with updated data
    # def post(self, request, album_id):
    #     if not request.user.is_authenticated():
    #         return render(request, 'music/login.html')
    #     else:
    #         form = AlbumForm(request.POST or None, request.FILES or None)
    #         # form = self.form_class(request.POST)
    #         if form.is_valid():
    #             album = form.save(commit=False)
    #             album.user = request.user
    #             album.album_logo = request.FILES['album_logo']
    #             file_type = album.album_logo.url.split('.')[-1]
    #             file_type = file_type.lower()
    #             if file_type not in IMAGE_FILE_TYPES:
    #                 context = {
    #                     'album': album,
    #                     'form': form,
    #                     'error_message': 'Image file must be PNG, JPG, or JPEG',
    #                 }
    #                 return render(request, 'music/album_update_form.html', context)
    #             album.save()
    #             return render(request, 'music/index.html', {'album': album})
    #         context = {
    #             "form": form,
    #         }
    #         return render(request, 'music/album_form.html', context)
    model = Album
    fields = ['artist', 'album_title', 'genre', 'album_logo', 'is_favorite']
    template_name_suffix = '_update_form'
    success_url = reverse_lazy('music:index')


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
        else:
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request, album_id):
        if not request.user.is_authenticated():
            return render(request, 'music/login.html')
        else:
            album = get_object_or_404(Album, pk=album_id)
            form = SongForm(request.POST or None, request.FILES or None)
            # form = self.form_class(request.POST)
            if form.is_valid():
                albums_songs = album.song_set.all()
                for song in albums_songs:
                    if song.song_title == form.cleaned_data.get("song_title"):
                        context = {
                            'album': album,
                            'form': form,
                            'error_message': 'You already added that song',
                        }
                        return render(request, 'music/song_form.html', context)
                song = form.save(commit=False)
                song.album = album
                song.audio_file = request.FILES['audio_file']
                file_type = song.audio_file.url.split('.')[-1]
                file_type = file_type.lower()
                if file_type not in AUDIO_FILE_TYPES:
                    context = {
                        'album': album,
                        'form': form,
                        'error_message': 'Audio file must be WAV, MP3, or OGG',
                    }
                    return render(request, 'music/song_form.html', context)
                song.save()
                # email = EmailMessage('Welcome to SongsIndia.com',
                #                      'Mail body',
                #                      settings.EMAIL_HOST_NAME,
                #                      [settings.EMAIL_HOST_NAME],
                #                      headers={'Message-ID': 'foo'})
                # email.send(fail_silently=True)
                # send_mail('Welcome to SongsIndia.com', 'Mail body', settings.EMAIL_HOST_NAME,
                #           [settings.EMAIL_HOST_NAME], fail_silently=True)
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
    # model = Song
    # success_url = reverse_lazy('music:detail')


def song_favorite(request, song_id, template):
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


class LoginView(FormView):
    """
    Provides the ability to login as a user with a username and password
    """
    template_name = 'music/login.html'
    success_url = '/music/'
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Sets a test cookie to make sure the user has cookies enabled
        request.session.set_test_cookie()

        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())

        # If the test cookie worked, go ahead and
        # delete it since its no longer needed
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()

        return super(LoginView, self).form_valid(form)

    def get_success_url(self):
        redirect_to = self.request.POST.get(self.redirect_field_name)
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = self.success_url
        return redirect_to


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/music/login/'

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return super(LogoutView, self).get(request, *args, **kwargs)
