import logging
from django.db.models import Q
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404

from music.models import Album, Song, User
from music.forms import AlbumForm, SongForm, AlbumFormUpdate
from music.utils.utils import select_next_pre_song, remove_file_logging

log = logging.getLogger(__name__)


class HomeView(View):
    template_name = 'music/home.html'

    def get(self, request):
        albums = Album.objects.all().order_by('album_title')
        query = request.GET.get('search')
        if query:
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
        if not request.user.is_authenticated:
            return render(request, self.template_name,
                {'albums': albums, 'is_authenticated': False})
        return render(request, self.template_name,
            {'albums': albums, 'is_authenticated': True})

class IndexView(View):
    template_name = 'music/index.html'

    def get(self, request):
        albums = Album.objects.all().order_by('album_title')
        query = request.GET.get('search')
        if query:
            log.info('searching for: %s' % query)
            albums = albums.filter(
                Q(album_title__icontains=query) |
                Q(artist__icontains=query)
            ).distinct()
        if not request.user.is_authenticated:
            return render(request, 'music/home.html', {'albums': albums})

        user = get_object_or_404(User, email=request.user)
        song_results = Song.objects.all()
        query = request.GET.get('search')
        if query:
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            if song_results:
                request.session['query'] = query
                return render(request, self.template_name,
                              {'song_results': song_results})
        return render(request, self.template_name,
                      {'albums': albums, 'user_name': user.first_name})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        query = request.session['query']
        if query:
            song_results = Song.objects.all()
            song_results = song_results.filter(
                Q(song_title__icontains=query)
            ).distinct()
            if song_results:
                context = {
                    'song_results': song_results,
                    'audio': str(self.request.POST.get('audio_url')),
                    'song_title': str(self.request.POST.get('song_title')),
                    'artist': str(self.request.POST.get('artist')),
                    'album_title': str(self.request.POST.get('album_title'))
                }
                return render(request, self.template_name, context)


class SongView(View):

    def get(self, request, filter_by):
        if not self.request.user.is_authenticated:
            return redirect('users:login')

        try:
            song_ids = []
            for album in Album.objects.all():
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            if filter_by == 'favorites':
                user_albums = Album.objects.filter(user=request.user)
                users_songs = users_songs.filter(Q(is_favorite=True) & Q(album__in=user_albums))
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'all_songs': users_songs,
            'filter_by': filter_by,
        })

    def post(self, request, filter_by):
        if not self.request.user.is_authenticated:
            return redirect('users:login')

        try:
            song_ids = []
            for album in Album.objects.all():
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            if filter_by == 'favorites':
                user_albums = Album.objects.filter(user=request.user)
                users_songs = users_songs.filter(Q(is_favorite=True) & Q(album__in=user_albums))
        except Album.DoesNotExist:
            users_songs = []

        context = {
            'all_songs': users_songs,
            'filter_by': filter_by,
            'audio': str(self.request.POST.get('audio_url')),
            'song_title': str(self.request.POST.get('song_title')),
            'artist': str(self.request.POST.get('artist')),
            'album_title': str(self.request.POST.get('album_title')),
            'audio_volume': str(self.request.POST.get('audio_volume'))
        }
        context = select_next_pre_song(users_songs, context)
        return render(request, 'music/songs.html', context)


class DetailView(View):
    template_name = 'music/detail.html'

    def get(self, request, album_id):
        if not request.user.is_authenticated:
            album = get_object_or_404(Album, id=album_id)
            return render(request, 'music/detail_visitor.html',
                {'album': album, 'is_authenticated': False})

        album = get_object_or_404(Album, id=album_id)
        return render(request, self.template_name,
            {'album': album, 'is_authenticated': True})

    def post(self, request, album_id):
        context = {
            'audio': str(self.request.POST.get('audio_url')),
            'song_title': str(self.request.POST.get('song_title')),
            'artist': str(self.request.POST.get('artist')),
            'album_title': str(self.request.POST.get('album_title')),
            'audio_volume': str(self.request.POST.get('audio_volume'))
        }
        if not request.user.is_authenticated:
            album = get_object_or_404(Album, id=album_id)
            context['album'] = album
            context['is_authenticated'] = False
            context = select_next_pre_song(album.song_set.all(), context)
            return render(request, 'music/detail_visitor.html', context)

        album = get_object_or_404(Album, id=album_id)
        context['album'] = album
        context['is_authenticated'] = True
        context = select_next_pre_song(album.song_set.all(), context)
        return render(request, self.template_name, context)


class AlbumCreate(View):
    form_class = AlbumForm
    template_name = 'music/album_form.html'

    # Display blank form
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.save()
            log.debug("'{0}' added album: '{1}' successfully.".format(
                request.user, album))
            return redirect('music:index')

        return render(request, self.template_name, {'form': form})


class AlbumUpdateView(View):
    template_name = 'music/album_update_form.html'

    def get(self, request, album_id):
        if not request.user.is_authenticated:
            return redirect('users:login')

        album = get_object_or_404(Album, id=album_id)
        form = AlbumFormUpdate(instance=album)
        return render(request, self.template_name, {'form': form})

    def post(self, request, album_id):
        album = get_object_or_404(Album, id=album_id, user=request.user)
        existing_logo = album.album_logo.url
        form = AlbumFormUpdate(request.POST or None, request.FILES or None, instance=album)
        if form.is_valid():
            form.save(commit=False)
            if request.FILES:
                remove_file_logging(existing_logo)
            album.save()
            log.debug("'{0}' updated album: '{1}' successfully.".format(
                request.user, album))
            return redirect('music:index')

        return render(request, self.template_name, {'form': form})


class AlbumDelete(View):

    def post(self, request, album_id):
        if not request.user.is_authenticated:
            return redirect('users:login')

        album = get_object_or_404(Album, id=album_id, user=request.user)
        # Deleting all songs under the album
        for song in album.song_set.all():
            remove_file_logging(song.audio_file.url)
            song.delete()

        # Deleting album
        remove_file_logging(album.album_logo.url)
        album.delete()
        log.debug("'{0}' deleted album: '{1}' successfully.".format(
            request.user, album))
        return redirect('music:index')


class SongCreate(View):
    form_class = SongForm
    template_name = 'music/song_form.html'

    # Display blank form
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        form = self.form_class
        form.base_fields['album'].queryset = Album.objects.filter(user=request.user)
        return render(request, self.template_name, {'form': form})

    # Process form data
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('users:login')

        form = SongForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album_id = int(request.POST.get('album'))
            album = get_object_or_404(Album, id=album_id)
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
            song.save()
            log.debug("'{0}' added song: '{1}' to album: '{2}' successfully.".format(
                request.user, song, album))
            context = {
                'album': album,
                'is_authenticated': True
            }
            return render(request, 'music/detail.html', context)
        context = {
            'form': form
        }
        return render(request, self.template_name, context)


class SongDelete(View):

    def post(self, request, album_id, song_id):
        if not request.user.is_authenticated:
            return redirect('users:login')

        album = get_object_or_404(Album, id=album_id)
        song = get_object_or_404(Song, id=song_id)
        # Deleting song
        remove_file_logging(song.audio_file.url)
        song.delete()
        log.debug("'{0}' deleted song: '{1}' from album: '{2}' successfully.".format(
            request.user, song, album))
        return render(request, 'music/detail.html',
            {'album': album, 'is_authenticated': True})


class SongFavoriteView(View):

    def post(self, request, filter_by):
        if not request.user.is_authenticated:
            return redirect('users:login')
        song_ids = []
        albums = Album.objects.all()
        song_id = request.POST.get('song_id')
        template = request.POST.get('template')
        for album in albums:
            for song in album.song_set.all():
                song_ids.append(song.pk)
        songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
        song = get_object_or_404(Song, pk=song_id)
        try:
            if song.is_favorite:
                song.is_favorite = False
            else:
                song.is_favorite = True
            song.save()
            log.debug("'{0}' updated song: {1} to album: '{2}' successfully.".format(
                request.user, song, song.album))
        except (KeyError, Song.DoesNotExist):
            if template == 'songs':
                return render(request, 'music/songs.html',
                              {'all_songs': songs,
                               'filter_by': filter_by,
                               'error_message': 'Song does not exists'})
            else:
                return render(request, 'music/detail.html',
                              {'albums': albums,
                               'filter_by': filter_by,
                               'is_authenticated': True,
                               'error_message': 'Song does not exists'})
        for album in albums:
            for song in album.song_set.all():
                song_ids.append(song.pk)
        if template == 'songs':
            if filter_by == 'all':
                songs = Song.objects.filter(pk__in=song_ids).order_by('song_title')
            else:
                user_albums = Album.objects.filter(user=request.user)
                songs = Song.objects.filter(
                    Q(pk__in=song_ids) & Q(album__in=user_albums) & Q(is_favorite=True))
            return render(request, 'music/songs.html',
                          {'all_songs': songs,
                           'filter_by': filter_by})
        else:
            album = get_object_or_404(Album, pk=song.album_id)
            return render(request, 'music/detail.html',
                          {'album': album, 'filter_by': filter_by,
                           'is_authenticated': True})


class AlbumFavoriteView(View):

    def get(self, request, album_id):
        if not request.user.is_authenticated:
            return redirect('users:login')

        albums = Album.objects.all().order_by('album_title')
        album = get_object_or_404(Album, pk=album_id)
        try:
            if album.is_favorite:
                album.is_favorite = False
            else:
                album.is_favorite = True
            album.save()
            log.debug("'{0}' updated album: '{1}' successfully.".format(
                request.user, album))
        except (KeyError, Album.DoesNotExist):
            context = {
                'albums': albums,
                'user_name': album.user.first_name,
                'error_message': 'Album does not exists.',
            }
            return render(request, 'music/index.html', context)
        else:
            return redirect('music:index')
